import asyncio
import os
import sys
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.tokenization.application.template_catalog_service import TemplateCatalogService
from app.services.tokenization.domain.entities.template_status import TemplateStatus
from app.services.tokenization.domain.exceptions import (
    TemplateAlreadyExistsError,
    TemplateCloneError,
    TemplateConsistencyError,
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


def _create_base_template(service: TemplateCatalogService, name: str = "Base Token"):
    return asyncio.run(service.create_template(
        email=TEST_EMAIL,
        name=name,
        description="Base template for testing",
        category="loyalty",
        strategy="retention",
        token_standard="ERC20",
        token_model={
            "standard": "ERC20",
            "name": name,
            "symbol": name[:8].upper(),
            "decimals": 18,
            "initial_supply": 1000000,
            "max_supply": 10000000,
            "mintable": True,
            "burnable": True,
        },
        characteristics={
            "target_use_case": "loyalty",
            "industry": "retail",
        },
        business_rules=[
            {
                "rule_id": "rule-1",
                "name": "Transfer Limit",
                "description": "Max transfer per day",
                "rule_type": "transfer_restriction",
                "parameters": {"restriction_type": "daily_limit", "max_amount": 10000},
            }
        ],
    ))


class TestCloneTemplate:
    def test_clone_creates_new_template(self, service: TemplateCatalogService):
        _create_base_template(service)
        cloned = asyncio.run(service.clone_template(
            email=TEST_EMAIL,
            source_name="Base Token",
            new_name="Cloned Token",
        ))
        assert cloned.name == "Cloned Token"
        assert cloned.parent_template_id is not None
        assert cloned.is_derived is True

    def test_clone_with_overrides(self, service: TemplateCatalogService):
        _create_base_template(service)
        cloned = asyncio.run(service.clone_template(
            email=TEST_EMAIL,
            source_name="Base Token",
            new_name="Custom Token",
            overrides={
                "description": "Custom description",
                "token_model": {"initial_supply": 500000},
            },
        ))
        assert cloned.description == "Custom description"
        assert cloned.token_model.initial_supply == 500000
        assert "description" in cloned.overridden_fields
        assert "token_model" in cloned.overridden_fields

    def test_clone_preserves_inherited_fields(self, service: TemplateCatalogService):
        _create_base_template(service)
        cloned = asyncio.run(service.clone_template(
            email=TEST_EMAIL,
            source_name="Base Token",
            new_name="Inherited Token",
        ))
        assert cloned.category == "loyalty"
        assert cloned.strategy == "retention"
        assert cloned.token_standard == "ERC20"
        assert cloned.overridden_fields == set()

    def test_clone_duplicate_name_raises(self, service: TemplateCatalogService):
        _create_base_template(service)
        with pytest.raises(TemplateAlreadyExistsError):
            asyncio.run(service.clone_template(
                email=TEST_EMAIL,
                source_name="Base Token",
                new_name="Base Token",
            ))

    def test_clone_nonexistent_source_raises(self, service: TemplateCatalogService):
        with pytest.raises(TemplateNotFoundError):
            asyncio.run(service.clone_template(
                email=TEST_EMAIL,
                source_name="Nonexistent",
                new_name="New Token",
            ))

    def test_clone_inheritance_chain(self, service: TemplateCatalogService):
        _create_base_template(service, "Level 0")
        asyncio.run(service.clone_template(
            email=TEST_EMAIL,
            source_name="Level 0",
            new_name="Level 1",
        ))
        asyncio.run(service.clone_template(
            email=TEST_EMAIL,
            source_name="Level 1",
            new_name="Level 2",
            overrides={"description": "Level 2 custom"},
        ))
        cloned = asyncio.run(service.get_template(TEST_EMAIL, "Level 2"))
        assert cloned.is_derived is True
        assert cloned.overridden_fields == {"description"}


class TestValidateTemplate:
    def test_valid_template(self, service: TemplateCatalogService):
        _create_base_template(service)
        result = asyncio.run(service.validate_template(TEST_EMAIL, "Base Token"))
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["template_name"] == "Base Token"

    def test_invalid_initial_supply_exceeds_max(self, service: TemplateCatalogService):
        with pytest.raises(ValidationError, match="initial_supply.*cannot exceed"):
            asyncio.run(service.create_template(
                email=TEST_EMAIL,
                name="Bad Token",
                description="d",
                category="c",
                strategy="s",
                token_standard="ERC20",
                token_model={
                    "standard": "ERC20",
                    "name": "Bad Token",
                    "symbol": "BAD",
                    "initial_supply": 2000,
                    "max_supply": 1000,
                    "mintable": True,
                },
            ))

    def test_burnable_without_mintable_raises(self, service: TemplateCatalogService):
        with pytest.raises(ValidationError, match="burnable requires mintable"):
            asyncio.run(service.create_template(
                email=TEST_EMAIL,
                name="Bad Token 2",
                description="d",
                category="c",
                strategy="s",
                token_standard="ERC20",
                token_model={
                    "standard": "ERC20",
                    "name": "Bad Token 2",
                    "symbol": "BAD2",
                    "burnable": True,
                    "mintable": False,
                },
            ))

    def test_nonexistent_template_raises(self, service: TemplateCatalogService):
        with pytest.raises(TemplateNotFoundError):
            asyncio.run(service.validate_template(TEST_EMAIL, "Nonexistent"))


class TestTemplateLineage:
    def test_single_template_lineage(self, service: TemplateCatalogService):
        _create_base_template(service)
        chain = asyncio.run(service.get_template_lineage(TEST_EMAIL, "Base Token"))
        assert len(chain) == 1
        assert chain[0]["name"] == "Base Token"
        assert chain[0]["overridden_fields"] == []

    def test_derived_template_lineage(self, service: TemplateCatalogService):
        _create_base_template(service)
        asyncio.run(service.clone_template(
            email=TEST_EMAIL,
            source_name="Base Token",
            new_name="Derived Token",
            overrides={"description": "Custom"},
        ))
        chain = asyncio.run(service.get_template_lineage(TEST_EMAIL, "Derived Token"))
        assert len(chain) == 2
        assert chain[0]["name"] == "Derived Token"
        assert chain[0]["overridden_fields"] == ["description"]
        assert chain[1]["name"] == "Base Token"
        assert chain[1]["overridden_fields"] == []

    def test_three_level_lineage(self, service: TemplateCatalogService):
        _create_base_template(service, "Gen 0")
        asyncio.run(service.clone_template(
            email=TEST_EMAIL,
            source_name="Gen 0",
            new_name="Gen 1",
            overrides={"description": "Gen 1 custom"},
        ))
        asyncio.run(service.clone_template(
            email=TEST_EMAIL,
            source_name="Gen 1",
            new_name="Gen 2",
            overrides={"category": "reward"},
        ))
        chain = asyncio.run(service.get_template_lineage(TEST_EMAIL, "Gen 2"))
        assert len(chain) == 3
        assert chain[0]["name"] == "Gen 2"
        assert chain[1]["name"] == "Gen 1"
        assert chain[2]["name"] == "Gen 0"

    def test_nonexistent_template_raises(self, service: TemplateCatalogService):
        with pytest.raises(TemplateNotFoundError):
            asyncio.run(service.get_template_lineage(TEST_EMAIL, "Nonexistent"))
