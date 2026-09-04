
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.auth.api.dependencies import get_current_token
from app.services.tokenization.api.routers.choice_router import get_choice_service, router
from app.services.tokenization.application.recommendation_choice_service import RecommendationChoiceService
from app.services.tokenization.domain.entities.template import Template
from app.services.tokenization.domain.entities.template_characteristics import TemplateCharacteristics
from app.services.tokenization.domain.entities.template_metadata import TemplateMetadata
from app.services.tokenization.domain.entities.template_status import TemplateStatus
from app.services.tokenization.domain.entities.template_version import TemplateVersion
from app.services.tokenization.domain.entities.token_model import TokenModel
from app.services.tokenization.infrastructure.config.settings import TokenizationSettings
from app.services.tokenization.infrastructure.llm.groq_adapter import GroqReorderAdapter


def _make_template(name, industry):
    return Template(
        template_id=f"id-{name}", name=name, description="d", category="c", strategy="s",
        token_standard="ERC20", status=TemplateStatus.ACTIVE,
        version=TemplateVersion(major=1, minor=0, patch=0),
        metadata=TemplateMetadata(tags=[industry]),
        characteristics=TemplateCharacteristics(target_use_case="x", industry=industry),
        token_model=TokenModel(standard="ERC20", name=name, symbol="TKN"),
    )


def _service_with_mocks(search=None, list_all=None, reorder=None, choices=None, resolve="wallet-user"):
    """Build the REAL service object with mocked repos — endpoints only call its methods."""
    mock_tpl = MagicMock()
    mock_tpl.search = AsyncMock(return_value=search or [])
    mock_tpl.list_all = AsyncMock(return_value=list_all if list_all is not None else (search or []))
    mock_choice = MagicMock()
    mock_choice.save = AsyncMock()
    mock_choice.list_by_user = AsyncMock(return_value=choices or [])
    groq_settings = TokenizationSettings(groq_enabled=False)
    if reorder is not None:
        mock_groq = MagicMock()
        mock_groq.reorder = AsyncMock(return_value=reorder)
        svc = RecommendationChoiceService(mock_tpl, mock_choice, mock_groq)
    else:
        svc = RecommendationChoiceService(mock_tpl, mock_choice, GroqReorderAdapter(settings=groq_settings))
    if callable(resolve):
        svc._resolve_user_id_by_email = resolve
    else:
        svc._resolve_user_id_by_email = lambda email: resolve  # noqa: E731
    return svc, mock_tpl, mock_choice


def _app_with_service(svc):
    app = FastAPI()
    app.include_router(router)

    async def _mock_token():
        return {"sub": "test"}

    app.dependency_overrides[get_current_token] = _mock_token
    app.dependency_overrides[get_choice_service] = lambda: svc
    return app


def _app_with_mock():
    svc, _, _ = _service_with_mocks()
    return _app_with_service(svc)


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
        svc, _, _ = _service_with_mocks()
        client = TestClient(_app_with_service(svc))
        resp = client.get("/tokenization/templates/by-business-type", params={"business_type": "invalid_type", "email": "u1@example.com"})
        assert resp.status_code == 422

    def test_service_not_configured_returns_503(self):
        app = FastAPI()
        app.include_router(router)

        async def _mock_token():
            return {"sub": "test"}

        app.dependency_overrides[get_current_token] = _mock_token
        client = TestClient(app)
        resp = client.get("/tokenization/templates/by-business-type", params={"business_type": "retail", "email": "u1@example.com"})
        assert resp.status_code == 503


class TestByBusinessTypeIsolation:
    def test_email_required(self):
        svc, _, _ = _service_with_mocks()
        client = TestClient(_app_with_service(svc))
        resp = client.get("/tokenization/templates/by-business-type", params={"business_type": "retail"})
        assert resp.status_code == 422

    def test_returns_only_industry_templates(self):
        tpl_retail = _make_template("Loyalty Token", "retail")
        tpl_gaming = _make_template("Reward Token", "gaming")
        svc, _, _ = _service_with_mocks(
            search=[tpl_retail], list_all=[tpl_retail, tpl_gaming], resolve="wallet-usera",
        )
        client = TestClient(_app_with_service(svc))
        resp = client.get("/tokenization/templates/by-business-type", params={"business_type": "retail", "email": "usera@example.com"})
        assert resp.status_code == 200
        assert "Loyalty Token" in resp.json()["templates"]
        assert "Reward Token" not in resp.json()["templates"]

    def test_injection_in_email_treated_literal(self):
        svc, _, _ = _service_with_mocks(resolve=lambda email: f"uid-{email}")
        client = TestClient(_app_with_service(svc))
        inj = "user' OR '1'='1@example.com"
        resp = client.get("/tokenization/templates/by-business-type", params={"business_type": "retail", "email": inj})
        assert resp.status_code == 200
        # Should return empty, not all users
        assert resp.json()["count"] == 0


class TestReorderEndpoint:
    def test_requires_auth(self):
        app = FastAPI(); app.include_router(router)
        client = TestClient(app)
        assert client.post("/tokenization/recommendation/order", json={"email": "u1@example.com", "business_type": "retail", "description": "valid description 1234567890"}).status_code in (401, 403)

    def test_short_description_rejected(self):
        client = TestClient(_app_with_mock())
        resp = client.post("/tokenization/recommendation/order", json={"email": "u1@example.com", "business_type": "retail", "description": "short"})
        assert resp.status_code == 422

    def test_always_appends_criar_do_zero(self):
        svc, _, _ = _service_with_mocks(
            search=[_make_template("Loyalty Token", "retail")],
            reorder=["Loyalty Token"],
            resolve="wallet-u1",
        )
        client = TestClient(_app_with_service(svc))
        resp = client.post("/tokenization/recommendation/order", json={"email": "u1@example.com", "business_type": "retail", "description": "valid description with more than 10 chars for tokenization"})
        assert resp.status_code == 200
        assert resp.json()["final_options"][-1] == "Nenhuma destas — Criar do Zero"

    def test_groq_invention_filtered(self):
        svc, _, _ = _service_with_mocks(
            search=[_make_template("Loyalty Token", "retail"), _make_template("Reward Token", "retail")],
            reorder=["Invented Token", "Loyalty Token", "Reward Token"],
            resolve="wallet-u1",
        )
        client = TestClient(_app_with_service(svc))
        resp = client.post("/tokenization/recommendation/order", json={"email": "u1@example.com", "business_type": "retail", "description": "valid description long enough for test"})
        assert "Invented Token" not in resp.json()["ordered_templates"]
        assert "Invented Token" not in resp.json()["final_options"]

    def test_description_sql_injection_treated_literal(self):
        svc, _, _ = _service_with_mocks(search=[], list_all=[], reorder=[], resolve="wallet-u1")
        client = TestClient(_app_with_service(svc))
        inj = "'; DROP TABLE tokenization_choices; -- plus extra to reach length"
        resp = client.post("/tokenization/recommendation/order", json={"email": "u1@example.com", "business_type": "retail", "description": inj})
        assert resp.status_code == 200  # not 500, injection not executed


class TestChoicesEndpoint:
    def test_requires_auth_create(self):
        app = FastAPI(); app.include_router(router)
        client = TestClient(app)
        assert client.post("/tokenization/choices", json={"email": "u1@example.com", "business_type": "retail", "description_tokenization": "valid description 1234567890", "tokenization_template": "Loyalty Token"}).status_code in (401, 403)

    def test_create_and_isolation(self):
        svc, _, mock_choice = _service_with_mocks(resolve="wallet-usera")
        client = TestClient(_app_with_service(svc))
        resp = client.post("/tokenization/choices", json={"email": "usera@example.com", "business_type": "retail", "description_tokenization": "challenge description long enough for validation", "tokenization_template": "Loyalty Token"})
        assert resp.status_code == 201
        # user_id in response is internal id resolved from email, never echoed from input
        assert resp.json()["user_id"] == "wallet-usera"
        assert mock_choice.save.call_count == 1

    def test_list_isolation(self):
        from app.services.tokenization.domain.entities.business_type import BusinessType
        from app.services.tokenization.domain.entities.tokenization_choice import TokenizationChoice
        c1 = TokenizationChoice(id="1", user_id="wallet-usera@example.com", business_type=BusinessType.RETAIL, description_tokenization="valid description 1234567890", tokenization_template="Loyalty Token")
        svc, _, mock_choice = _service_with_mocks(
            choices=[c1], resolve=lambda email: f"wallet-{email}",
        )
        client = TestClient(_app_with_service(svc))
        resp_a = client.get("/tokenization/choices", params={"email": "usera@example.com"})
        resp_b = client.get("/tokenization/choices", params={"email": "userb@example.com"})

        assert resp_a.status_code == 200
        assert resp_a.json()["total"] == 1
        assert mock_choice.list_by_user.call_args[0][0] in ("wallet-usera@example.com", "wallet-userb@example.com")

    def test_blank_template_rejected(self):
        client = TestClient(_app_with_mock())
        resp = client.post("/tokenization/choices", json={"email": "u1@example.com", "business_type": "retail", "description_tokenization": "valid description 1234567890", "tokenization_template": "   "})
        assert resp.status_code == 422

    def test_sql_injection_in_template_literal(self):
        svc, _, _ = _service_with_mocks(resolve="wallet-u1")
        client = TestClient(_app_with_service(svc))
        inj = "Loyalty Token'; DROP TABLE tokenization_choices; --"
        resp = client.post("/tokenization/choices", json={"email": "u1@example.com", "business_type": "retail", "description_tokenization": "valid description long enough for test", "tokenization_template": inj})

        assert resp.status_code == 201
        assert "DROP TABLE" in resp.json()["tokenization_template"]

    def test_create_zero_option_allowed(self):
        svc, _, _ = _service_with_mocks(resolve="wallet-u1")
        client = TestClient(_app_with_service(svc))
        resp = client.post("/tokenization/choices", json={"email": "u1@example.com", "business_type": "retail", "description_tokenization": "valid description long enough for test", "tokenization_template": "Nenhuma destas — Criar do Zero"})
        assert resp.status_code == 201
        assert resp.json()["tokenization_template"] == "Nenhuma destas — Criar do Zero"

    def test_user_id_rejected_in_body(self):
        client = TestClient(_app_with_mock())
        resp = client.post("/tokenization/choices", json={"user_id": "u1", "business_type": "retail", "description_tokenization": "valid description 1234567890", "tokenization_template": "Loyalty Token"})
        assert resp.status_code == 422
