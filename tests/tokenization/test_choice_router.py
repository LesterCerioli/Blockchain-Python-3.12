
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.auth.api.dependencies import get_current_token
from app.services.tokenization.api.routers.choice_router import router
from app.services.tokenization.domain.entities.template import Template
from app.services.tokenization.domain.entities.template_characteristics import TemplateCharacteristics
from app.services.tokenization.domain.entities.template_metadata import TemplateMetadata
from app.services.tokenization.domain.entities.template_status import TemplateStatus
from app.services.tokenization.domain.entities.template_version import TemplateVersion
from app.services.tokenization.domain.entities.token_model import TokenModel


def _make_template(name, industry):
    return Template(
        template_id=f"id-{name}", name=name, description="d", category="c", strategy="s",
        token_standard="ERC20", status=TemplateStatus.ACTIVE,
        version=TemplateVersion(major=1, minor=0, patch=0),
        metadata=TemplateMetadata(tags=[industry]),
        characteristics=TemplateCharacteristics(target_use_case="x", industry=industry),
        token_model=TokenModel(standard="ERC20", name=name, symbol="TKN"),
    )


def _app_with_mock():
    app = FastAPI()
    app.include_router(router)
    async def _mock_token():
        return {"sub": "test"}
    app.dependency_overrides[get_current_token] = _mock_token
    return app


class TestBusinessTypesEndpoint:
    def test_requires_auth(self):
        app = FastAPI(); app.include_router(router)
        client = TestClient(app)
        assert client.get("/tokenization/business-types").status_code in (401, 403)

    def test_returns_all_types(self):
        client = TestClient(_app_with_mock())
        resp = client.get("/tokenization/business-types")
        assert resp.status_code == 200
        vals = [b["value"] for b in resp.json()["business_types"]]
        assert "retail" in vals and "fintech" in vals and "other" in vals

    def test_invalid_business_type_rejected(self):
        with patch("app.services.tokenization.api.routers.choice_router.DynamoDBTemplateRepository") as MockTpl, \
             patch("app.services.tokenization.api.routers.choice_router.DynamoDBChoiceRepository"), \
             patch("app.services.tokenization.api.routers.choice_router.GroqReorderAdapter"):
            MockTpl.return_value.search = AsyncMock(return_value=[])
            MockTpl.return_value.list_all = AsyncMock(return_value=[])
            client = TestClient(_app_with_mock())
            resp = client.get("/tokenization/templates/by-business-type", params={"business_type": "invalid_type", "user_id": "u1"})
            assert resp.status_code == 422


class TestByBusinessTypeIsolation:
    def test_user_id_required(self):
        with patch("app.services.tokenization.api.routers.choice_router.DynamoDBTemplateRepository") as MockTpl, \
             patch("app.services.tokenization.api.routers.choice_router.DynamoDBChoiceRepository"), \
             patch("app.services.tokenization.api.routers.choice_router.GroqReorderAdapter"):
            MockTpl.return_value.search = AsyncMock(return_value=[])
            MockTpl.return_value.list_all = AsyncMock(return_value=[])
            client = TestClient(_app_with_mock())
            resp = client.get("/tokenization/templates/by-business-type", params={"business_type": "retail"})
            assert resp.status_code == 422

    def test_returns_only_industry_templates(self):
        with patch("app.services.tokenization.api.routers.choice_router.DynamoDBTemplateRepository") as MockTpl, \
             patch("app.services.tokenization.api.routers.choice_router.DynamoDBChoiceRepository"), \
             patch("app.services.tokenization.api.routers.choice_router.GroqReorderAdapter"):
            tpl_retail = _make_template("Loyalty Token", "retail")
            tpl_gaming = _make_template("Reward Token", "gaming")
            MockTpl.return_value.search = AsyncMock(return_value=[tpl_retail])
            MockTpl.return_value.list_all = AsyncMock(return_value=[tpl_retail, tpl_gaming])
            MockTpl.return_value.search = AsyncMock(return_value=[tpl_retail])
            client = TestClient(_app_with_mock())
            resp = client.get("/tokenization/templates/by-business-type", params={"business_type": "retail", "user_id": "userA"})
            assert resp.status_code == 200
            assert "Loyalty Token" in resp.json()["templates"]
            assert "Reward Token" not in resp.json()["templates"]

    def test_injection_in_user_id_treated_literal(self):
        with patch("app.services.tokenization.api.routers.choice_router.DynamoDBTemplateRepository") as MockTpl, \
             patch("app.services.tokenization.api.routers.choice_router.DynamoDBChoiceRepository"), \
             patch("app.services.tokenization.api.routers.choice_router.GroqReorderAdapter"):
            MockTpl.return_value.search = AsyncMock(return_value=[])
            MockTpl.return_value.list_all = AsyncMock(return_value=[])
            client = TestClient(_app_with_mock())
            inj = "user' OR '1'='1"
            resp = client.get("/tokenization/templates/by-business-type", params={"business_type": "retail", "user_id": inj})
            assert resp.status_code == 200
            # Should return empty, not all users
            assert resp.json()["count"] == 0


class TestReorderEndpoint:
    def test_requires_auth(self):
        app = FastAPI(); app.include_router(router)
        client = TestClient(app)
        assert client.post("/tokenization/recommendation/order", json={"user_id": "u1", "business_type": "retail", "description": "valid description 1234567890"}).status_code in (401, 403)

    def test_short_description_rejected(self):
        client = TestClient(_app_with_mock())
        resp = client.post("/tokenization/recommendation/order", json={"user_id": "u1", "business_type": "retail", "description": "short"})
        assert resp.status_code == 422

    def test_always_appends_criar_do_zero(self):
        with patch("app.services.tokenization.api.routers.choice_router.DynamoDBTemplateRepository") as MockTpl, \
             patch("app.services.tokenization.api.routers.choice_router.DynamoDBChoiceRepository"), \
             patch("app.services.tokenization.api.routers.choice_router.GroqReorderAdapter") as MockGroq:
            MockTpl.return_value.search = AsyncMock(return_value=[_make_template("Loyalty Token", "retail")])
            MockTpl.return_value.list_all = AsyncMock(return_value=[_make_template("Loyalty Token", "retail")])
            MockGroq.return_value.reorder = AsyncMock(return_value=["Loyalty Token"])
            client = TestClient(_app_with_mock())
            resp = client.post("/tokenization/recommendation/order", json={"user_id": "u1", "business_type": "retail", "description": "valid description with more than 10 chars for tokenization"})
            assert resp.status_code == 200
            assert resp.json()["final_options"][-1] == "Nenhuma destas — Criar do Zero"

    def test_groq_invention_filtered(self):
        with patch("app.services.tokenization.api.routers.choice_router.DynamoDBTemplateRepository") as MockTpl, \
             patch("app.services.tokenization.api.routers.choice_router.DynamoDBChoiceRepository"), \
             patch("app.services.tokenization.api.routers.choice_router.GroqReorderAdapter") as MockGroq:
            MockTpl.return_value.search = AsyncMock(return_value=[_make_template("Loyalty Token", "retail"), _make_template("Reward Token", "retail")])
            MockTpl.return_value.list_all = AsyncMock(return_value=[_make_template("Loyalty Token", "retail"), _make_template("Reward Token", "retail")])
            MockGroq.return_value.reorder = AsyncMock(return_value=["Invented Token", "Loyalty Token", "Reward Token"])
            client = TestClient(_app_with_mock())
            resp = client.post("/tokenization/recommendation/order", json={"user_id": "u1", "business_type": "retail", "description": "valid description long enough for test"})
            assert "Invented Token" not in resp.json()["ordered_templates"]
            assert "Invented Token" not in resp.json()["final_options"]

    def test_description_sql_injection_treated_literal(self):
        with patch("app.services.tokenization.api.routers.choice_router.DynamoDBTemplateRepository") as MockTpl, \
             patch("app.services.tokenization.api.routers.choice_router.DynamoDBChoiceRepository"), \
             patch("app.services.tokenization.api.routers.choice_router.GroqReorderAdapter") as MockGroq:
            MockTpl.return_value.search = AsyncMock(return_value=[])
            MockTpl.return_value.list_all = AsyncMock(return_value=[])
            MockGroq.return_value.reorder = AsyncMock(return_value=[])
            client = TestClient(_app_with_mock())
            inj = "'; DROP TABLE tokenization_choices; -- plus extra to reach length"
            resp = client.post("/tokenization/recommendation/order", json={"user_id": "u1", "business_type": "retail", "description": inj})
            assert resp.status_code == 200  # not 500, injection not executed


class TestChoicesEndpoint:
    def test_requires_auth_create(self):
        app = FastAPI(); app.include_router(router)
        client = TestClient(app)
        assert client.post("/tokenization/choices", json={"user_id": "u1", "business_type": "retail", "description_tokenization": "valid description 1234567890", "tokenization_template": "Loyalty Token"}).status_code in (401, 403)

    def test_create_and_isolation(self):
        with patch("app.services.tokenization.api.routers.choice_router.DynamoDBTemplateRepository"), \
             patch("app.services.tokenization.api.routers.choice_router.DynamoDBChoiceRepository") as MockChoice, \
             patch("app.services.tokenization.api.routers.choice_router.GroqReorderAdapter"):
            MockChoice.return_value.save = AsyncMock()
            MockChoice.return_value.list_by_user = AsyncMock(return_value=[])
            client = TestClient(_app_with_mock())
            resp = client.post("/tokenization/choices", json={"user_id": "userA", "business_type": "retail", "description_tokenization": "challenge description long enough for validation", "tokenization_template": "Loyalty Token"})
            assert resp.status_code == 201
            assert resp.json()["user_id"] == "userA"
            
            assert MockChoice.return_value.save.call_count == 1

    def test_list_isolation(self):
        with patch("app.services.tokenization.api.routers.choice_router.DynamoDBTemplateRepository"), \
             patch("app.services.tokenization.api.routers.choice_router.DynamoDBChoiceRepository") as MockChoice, \
             patch("app.services.tokenization.api.routers.choice_router.GroqReorderAdapter"):
            from app.services.tokenization.domain.entities.business_type import BusinessType
            from app.services.tokenization.domain.entities.tokenization_choice import TokenizationChoice
            c1 = TokenizationChoice(id="1", user_id="userA", business_type=BusinessType.RETAIL, description_tokenization="valid description 1234567890", tokenization_template="Loyalty Token")
            MockChoice.return_value.list_by_user = AsyncMock(return_value=[c1])
            client = TestClient(_app_with_mock())
            resp_a = client.get("/tokenization/choices", params={"user_id": "userA"})
            resp_b = client.get("/tokenization/choices", params={"user_id": "userB"})
            
            assert resp_a.status_code == 200
            assert resp_a.json()["total"] == 1
            
            assert MockChoice.return_value.list_by_user.call_args[0][0] in ("userA", "userB")

    def test_blank_template_rejected(self):
        client = TestClient(_app_with_mock())
        resp = client.post("/tokenization/choices", json={"user_id": "u1", "business_type": "retail", "description_tokenization": "valid description 1234567890", "tokenization_template": "   "})
        assert resp.status_code == 422

    def test_sql_injection_in_template_literal(self):
        with patch("app.services.tokenization.api.routers.choice_router.DynamoDBTemplateRepository"), \
             patch("app.services.tokenization.api.routers.choice_router.DynamoDBChoiceRepository") as MockChoice, \
             patch("app.services.tokenization.api.routers.choice_router.GroqReorderAdapter"):
            MockChoice.return_value.save = AsyncMock()
            MockChoice.return_value.list_by_user = AsyncMock(return_value=[])
            client = TestClient(_app_with_mock())
            inj = "Loyalty Token'; DROP TABLE tokenization_choices; --"
            resp = client.post("/tokenization/choices", json={"user_id": "u1", "business_type": "retail", "description_tokenization": "valid description long enough for test", "tokenization_template": inj})
            
            assert resp.status_code == 201
            assert "DROP TABLE" in resp.json()["tokenization_template"]

    def test_create_zero_option_allowed(self):
        with patch("app.services.tokenization.api.routers.choice_router.DynamoDBTemplateRepository"), \
             patch("app.services.tokenization.api.routers.choice_router.DynamoDBChoiceRepository") as MockChoice, \
             patch("app.services.tokenization.api.routers.choice_router.GroqReorderAdapter"):
            MockChoice.return_value.save = AsyncMock()
            client = TestClient(_app_with_mock())
            resp = client.post("/tokenization/choices", json={"user_id": "u1", "business_type": "retail", "description_tokenization": "valid description long enough for test", "tokenization_template": "Nenhuma destas — Criar do Zero"})
            assert resp.status_code == 201
            assert resp.json()["tokenization_template"] == "Nenhuma destas — Criar do Zero"
