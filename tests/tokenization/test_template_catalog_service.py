import asyncio
import pytest
from unittest.mock import MagicMock

from app.services.tokenization.application.template_catalog_service import TemplateCatalogService
from app.services.tokenization.domain.entities.template_status import TemplateStatus
from app.services.tokenization.domain.exceptions import (
    ApprovalRequiredError,
    TemplateAlreadyExistsError,
    TemplateNotArchivableError,
    TemplateNotEditableError,
    TemplateNotFoundError,
)
from app.services.tokenization.infrastructure.repositories.in_memory_template_repository import InMemoryTemplateRepository

TEST_EMAIL = "test@example.com"
TEST_USER_ID = "test-user-123"


def _make_mock_users_client(user_id: str = TEST_USER_ID):
    mock_client = MagicMock()
    mock_client.query.return_value = {
        "Items": [{"user_id": {"S": user_id}}]
    }
    return mock_client


@pytest.fixture
def repo() -> InMemoryTemplateRepository:
    return InMemoryTemplateRepository()


@pytest.fixture
def service(repo: InMemoryTemplateRepository) -> TemplateCatalogService:
    return TemplateCatalogService(
        template_repository=repo,
        users_client=_make_mock_users_client(),
    )


class TestCreateTemplate:
    def test_creates_template(self, service: TemplateCatalogService):
        t = asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Loyalty Token",
            description="Loyalty rewards",
            category="loyalty",
            strategy="retention",
            token_standard="ERC20",
        ))
        assert t.name == "Loyalty Token"
        assert t.status == TemplateStatus.DRAFT
        assert t.version.to_string() == "1.0.0"

    def test_duplicate_name_raises(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Loyalty Token",
            description="Loyalty rewards",
            category="loyalty",
            strategy="retention",
            token_standard="ERC20",
        ))
        with pytest.raises(TemplateAlreadyExistsError):
            asyncio.run(service.create_template(
                email=TEST_EMAIL,
                name="Loyalty Token",
                description="Another",
                category="loyalty",
                strategy="retention",
                token_standard="ERC20",
            ))

    def test_invalid_email_raises(self, service: TemplateCatalogService):
        mock_client = MagicMock()
        mock_client.query.return_value = {"Items": []}
        service._users_client = mock_client
        with pytest.raises(TemplateNotFoundError):
            asyncio.run(service.create_template(
                email="nonexistent@example.com",
                name="Test",
                description="d",
                category="c",
                strategy="s",
                token_standard="ERC20",
            ))


class TestGetTemplate:
    def test_get_existing(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Test", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        fetched = asyncio.run(service.get_template(TEST_EMAIL, "Test"))
        assert fetched is not None
        assert fetched.name == "Test"

    def test_get_nonexistent_raises(self, service: TemplateCatalogService):
        with pytest.raises(TemplateNotFoundError):
            asyncio.run(service.get_template(TEST_EMAIL, "nonexistent"))


class TestUpdateTemplate:
    def test_update_draft(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Test", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        updated = asyncio.run(service.update_template(
            email=TEST_EMAIL,
            name="Test", description="Updated description"
        ))
        assert updated.description == "Updated description"

    def test_update_active_raises(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Test", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        asyncio.run(service.submit_for_review(TEST_EMAIL, "Test"))
        asyncio.run(service.approve_template(TEST_EMAIL, "Test", "admin"))
        asyncio.run(service.activate_template(TEST_EMAIL, "Test"))
        with pytest.raises(TemplateNotEditableError):
            asyncio.run(service.update_template(email=TEST_EMAIL, name="Test", description="X"))

    def test_update_nonexistent_raises(self, service: TemplateCatalogService):
        with pytest.raises(TemplateNotFoundError):
            asyncio.run(service.update_template(email=TEST_EMAIL, name="nonexistent", description="X"))


class TestArchiveTemplate:
    def test_archive_draft(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Test", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        archived = asyncio.run(service.archive_template(TEST_EMAIL, "Test"))
        assert archived.status == TemplateStatus.ARCHIVED

    def test_archive_already_archived_raises(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Test", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        asyncio.run(service.archive_template(TEST_EMAIL, "Test"))
        with pytest.raises(TemplateNotArchivableError):
            asyncio.run(service.archive_template(TEST_EMAIL, "Test"))


class TestApprovalWorkflow:
    def test_full_workflow(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Test", description="d", category="c", strategy="s", token_standard="ERC20"
        ))

        submitted = asyncio.run(service.submit_for_review(TEST_EMAIL, "Test"))
        assert submitted.status == TemplateStatus.PENDING_REVIEW

        approved = asyncio.run(service.approve_template(TEST_EMAIL, "Test", "admin"))
        assert approved.status == TemplateStatus.APPROVED
        assert approved.approved_by == "admin"

        activated = asyncio.run(service.activate_template(TEST_EMAIL, "Test"))
        assert activated.status == TemplateStatus.ACTIVE

    def test_submit_non_draft_raises(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Test", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        asyncio.run(service.submit_for_review(TEST_EMAIL, "Test"))
        with pytest.raises(TemplateNotEditableError):
            asyncio.run(service.submit_for_review(TEST_EMAIL, "Test"))

    def test_approve_non_pending_raises(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Test", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        with pytest.raises(TemplateNotEditableError):
            asyncio.run(service.approve_template(TEST_EMAIL, "Test", "admin"))

    def test_activate_non_approved_raises(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Test", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        with pytest.raises(ApprovalRequiredError):
            asyncio.run(service.activate_template(TEST_EMAIL, "Test"))


class TestDeprecateTemplate:
    def test_deprecate(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Test", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        deprecated = asyncio.run(service.deprecate_template(TEST_EMAIL, "Test"))
        assert deprecated.status == TemplateStatus.DEPRECATED


class TestBumpVersion:
    def test_bump_patch(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Test", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        bumped = asyncio.run(service.bump_version(TEST_EMAIL, "Test", "patch"))
        assert bumped.version.to_string() == "1.0.1"

    def test_bump_minor(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Test", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        bumped = asyncio.run(service.bump_version(TEST_EMAIL, "Test", "minor"))
        assert bumped.version.to_string() == "1.1.0"

    def test_bump_major(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Test", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        bumped = asyncio.run(service.bump_version(TEST_EMAIL, "Test", "major"))
        assert bumped.version.to_string() == "2.0.0"


class TestSearchAndList:
    def test_list_all(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="A", description="d", category="loyalty", strategy="s", token_standard="ERC20"
        ))
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="B", description="d", category="reward", strategy="s", token_standard="ERC20"
        ))
        all_templates = asyncio.run(service.list_templates(TEST_EMAIL))
        assert len(all_templates) == 2

    def test_list_by_category(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="A", description="d", category="loyalty", strategy="s", token_standard="ERC20"
        ))
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="B", description="d", category="reward", strategy="s", token_standard="ERC20"
        ))
        loyalty = asyncio.run(service.list_by_category(TEST_EMAIL, "loyalty"))
        assert len(loyalty) == 1
        assert loyalty[0].name == "A"

    def test_list_by_strategy(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="A", description="d", category="c", strategy="retention", token_standard="ERC20"
        ))
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="B", description="d", category="c", strategy="engagement", token_standard="ERC20"
        ))
        retention = asyncio.run(service.list_by_strategy(TEST_EMAIL, "retention"))
        assert len(retention) == 1

    def test_search_by_query(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Loyalty Token", description="For loyalty programs", category="loyalty", strategy="s", token_standard="ERC20"
        ))
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="Reward Token", description="For rewards", category="reward", strategy="s", token_standard="ERC20"
        ))
        results = asyncio.run(service.search_templates(email=TEST_EMAIL, query="loyalty"))
        assert len(results) == 1
        assert results[0].name == "Loyalty Token"

    def test_search_by_category(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="A", description="d", category="loyalty", strategy="s", token_standard="ERC20"
        ))
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="B", description="d", category="reward", strategy="s", token_standard="ERC20"
        ))
        results = asyncio.run(service.search_templates(email=TEST_EMAIL, category="reward"))
        assert len(results) == 1

    def test_search_by_token_standard(self, service: TemplateCatalogService):
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="A", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="B", description="d", category="c", strategy="s", token_standard="ERC721"
        ))
        results = asyncio.run(service.search_templates(email=TEST_EMAIL, token_standard="ERC721"))
        assert len(results) == 1

    def test_count(self, service: TemplateCatalogService):
        assert asyncio.run(service.count_templates(TEST_EMAIL)) == 0
        asyncio.run(service.create_template(
            email=TEST_EMAIL,
            name="A", description="d", category="c", strategy="s", token_standard="ERC20"
        ))
        assert asyncio.run(service.count_templates(TEST_EMAIL)) == 1
