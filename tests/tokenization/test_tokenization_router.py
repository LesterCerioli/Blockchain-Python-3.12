import asyncio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.services.auth.api.dependencies import get_current_token
from app.services.tokenization.api.routers.tokenization_router import router
from app.services.tokenization.application.template_catalog_service import TemplateCatalogService
from app.services.tokenization.infrastructure.repositories.in_memory_template_repository import InMemoryTemplateRepository

TEST_EMAIL = "test@example.com"
TEST_USER_ID = "test-user-123"


async def _mock_token():
    return {"sub": "test", "iss": "auth_service", "type": "m2m"}


def _make_mock_users_client(user_id: str = TEST_USER_ID):
    mock_client = MagicMock()
    mock_client.query.return_value = {
        "Items": [{"user_id": {"S": user_id}}]
    }
    return mock_client


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    repo = InMemoryTemplateRepository()
    app.state.tokenization_catalog_service = TemplateCatalogService(
        template_repository=repo,
        users_client=_make_mock_users_client(),
    )
    app.dependency_overrides[get_current_token] = _mock_token
    app.include_router(router)
    return TestClient(app)


class TestCreateTemplateEndpoint:
    def test_create_template(self, client: TestClient):
        response = client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "Loyalty Token",
                "description": "Loyalty rewards",
                "category": "loyalty",
                "strategy": "retention",
                "token_standard": "ERC20",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Loyalty Token"
        assert data["status"] == "draft"
        assert "template_id" not in data

    def test_create_duplicate_returns_409(self, client: TestClient):
        client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "Test",
                "description": "d",
                "category": "c",
                "strategy": "s",
                "token_standard": "ERC20",
            },
        )
        response = client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "Test",
                "description": "d",
                "category": "c",
                "strategy": "s",
                "token_standard": "ERC20",
            },
        )
        assert response.status_code == 409


class TestListTemplatesEndpoint:
    def test_list_empty(self, client: TestClient):
        response = client.get(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_with_templates(self, client: TestClient):
        client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "A",
                "description": "d",
                "category": "c",
                "strategy": "s",
                "token_standard": "ERC20",
            },
        )
        response = client.get(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1


class TestGetTemplateEndpoint:
    def test_get_existing(self, client: TestClient):
        client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "Test",
                "description": "d",
                "category": "c",
                "strategy": "s",
                "token_standard": "ERC20",
            },
        )
        response = client.get(
            "/v1/tokenization/templates/Test",
            params={"email": TEST_EMAIL},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Test"

    def test_get_nonexistent_returns_404(self, client: TestClient):
        response = client.get(
            "/v1/tokenization/templates/nonexistent",
            params={"email": TEST_EMAIL},
        )
        assert response.status_code == 404


class TestUpdateTemplateEndpoint:
    def test_update(self, client: TestClient):
        client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "Test",
                "description": "d",
                "category": "c",
                "strategy": "s",
                "token_standard": "ERC20",
            },
        )
        response = client.put(
            "/v1/tokenization/templates/Test",
            params={"email": TEST_EMAIL},
            json={"description": "Updated description"},
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

    def test_update_nonexistent_returns_404(self, client: TestClient):
        response = client.put(
            "/v1/tokenization/templates/nonexistent",
            params={"email": TEST_EMAIL},
            json={"description": "X"},
        )
        assert response.status_code == 404


class TestArchiveTemplateEndpoint:
    def test_archive(self, client: TestClient):
        client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "Test",
                "description": "d",
                "category": "c",
                "strategy": "s",
                "token_standard": "ERC20",
            },
        )
        response = client.delete(
            "/v1/tokenization/templates/Test",
            params={"email": TEST_EMAIL},
        )
        assert response.status_code == 204

    def test_archive_nonexistent_returns_404(self, client: TestClient):
        response = client.delete(
            "/v1/tokenization/templates/nonexistent",
            params={"email": TEST_EMAIL},
        )
        assert response.status_code == 404


class TestApprovalWorkflowEndpoint:
    def test_submit_approve_activate(self, client: TestClient):
        client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "Test",
                "description": "d",
                "category": "c",
                "strategy": "s",
                "token_standard": "ERC20",
            },
        )

        submit_resp = client.post(
            "/v1/tokenization/templates/Test/submit",
            params={"email": TEST_EMAIL},
        )
        assert submit_resp.status_code == 200
        assert submit_resp.json()["status"] == "pending_review"

        approve_resp = client.post(
            "/v1/tokenization/templates/Test/approve",
            params={"email": TEST_EMAIL},
            json={"approved_by": "admin"},
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "approved"

        activate_resp = client.post(
            "/v1/tokenization/templates/Test/activate",
            params={"email": TEST_EMAIL},
        )
        assert activate_resp.status_code == 200
        assert activate_resp.json()["status"] == "active"

    def test_activate_non_approved_returns_422(self, client: TestClient):
        client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "Test",
                "description": "d",
                "category": "c",
                "strategy": "s",
                "token_standard": "ERC20",
            },
        )
        response = client.post(
            "/v1/tokenization/templates/Test/activate",
            params={"email": TEST_EMAIL},
        )
        assert response.status_code == 422


class TestBumpVersionEndpoint:
    def test_bump_patch(self, client: TestClient):
        client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "Test",
                "description": "d",
                "category": "c",
                "strategy": "s",
                "token_standard": "ERC20",
            },
        )
        response = client.post(
            "/v1/tokenization/templates/Test/version",
            params={"email": TEST_EMAIL},
            json={"bump_type": "patch"},
        )
        assert response.status_code == 200
        assert response.json()["version"] == "1.0.1"


class TestDeprecateEndpoint:
    def test_deprecate(self, client: TestClient):
        client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "Test",
                "description": "d",
                "category": "c",
                "strategy": "s",
                "token_standard": "ERC20",
            },
        )
        response = client.post(
            "/v1/tokenization/templates/Test/deprecate",
            params={"email": TEST_EMAIL},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "deprecated"


class TestSearchEndpoint:
    def test_search(self, client: TestClient):
        client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "Loyalty Token",
                "description": "Loyalty",
                "category": "loyalty",
                "strategy": "retention",
                "token_standard": "ERC20",
            },
        )
        client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "Reward Token",
                "description": "Reward",
                "category": "reward",
                "strategy": "engagement",
                "token_standard": "ERC721",
            },
        )
        response = client.post(
            "/v1/tokenization/templates/search",
            params={"email": TEST_EMAIL},
            json={"category": "loyalty"},
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1


class TestListByCategoryEndpoint:
    def test_list_by_category(self, client: TestClient):
        client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "A",
                "description": "d",
                "category": "loyalty",
                "strategy": "s",
                "token_standard": "ERC20",
            },
        )
        response = client.get(
            "/v1/tokenization/templates/category/loyalty",
            params={"email": TEST_EMAIL},
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1


class TestListByStrategyEndpoint:
    def test_list_by_strategy(self, client: TestClient):
        client.post(
            "/v1/tokenization/templates",
            params={"email": TEST_EMAIL},
            json={
                "name": "A",
                "description": "d",
                "category": "c",
                "strategy": "retention",
                "token_standard": "ERC20",
            },
        )
        response = client.get(
            "/v1/tokenization/templates/strategy/retention",
            params={"email": TEST_EMAIL},
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1


class TestSeedCatalogEndpoint:
    def test_seed(self, client: TestClient):
        response = client.get(
            "/v1/tokenization/catalog/seed",
            params={"email": TEST_EMAIL},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["seeded"] > 0
