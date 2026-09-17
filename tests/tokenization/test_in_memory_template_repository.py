import asyncio
import pytest

from app.services.tokenization.domain.entities.template import Template
from app.services.tokenization.domain.entities.template_status import TemplateStatus
from app.services.tokenization.infrastructure.repositories.in_memory_template_repository import InMemoryTemplateRepository

TEST_USER_ID = "test-user-123"


def _make_template(template_id: str = "tpl-1", name: str = "Test", category: str = "loyalty", strategy: str = "retention", standard: str = "ERC20", created_by: str = TEST_USER_ID) -> Template:
    return Template(
        template_id=template_id,
        name=name,
        description="desc",
        category=category,
        strategy=strategy,
        token_standard=standard,
        created_by=created_by,
    )


class TestInMemoryTemplateRepository:
    def test_create_and_get(self):
        repo = InMemoryTemplateRepository()
        t = _make_template()
        asyncio.run(repo.create(t))
        fetched = asyncio.run(repo.get_by_id(TEST_USER_ID, "tpl-1"))
        assert fetched is not None
        assert fetched.name == "Test"

    def test_get_nonexistent_returns_none(self):
        repo = InMemoryTemplateRepository()
        assert asyncio.run(repo.get_by_id(TEST_USER_ID, "missing")) is None

    def test_get_by_name(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.create(_make_template()))
        found = asyncio.run(repo.get_by_name(TEST_USER_ID, "Test"))
        assert found is not None

    def test_get_by_name_case_insensitive(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.create(_make_template(name="My Token")))
        found = asyncio.run(repo.get_by_name(TEST_USER_ID, "my token"))
        assert found is not None

    def test_update(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.create(_make_template()))
        updated = _make_template(name="Updated")
        asyncio.run(repo.update(updated))
        fetched = asyncio.run(repo.get_by_id(TEST_USER_ID, "tpl-1"))
        assert fetched.name == "Updated"

    def test_delete(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.create(_make_template()))
        asyncio.run(repo.delete(TEST_USER_ID, "tpl-1"))
        assert asyncio.run(repo.get_by_id(TEST_USER_ID, "tpl-1")) is None

    def test_delete_nonexistent_no_error(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.delete(TEST_USER_ID, "missing"))

    def test_list_all(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.create(_make_template(template_id="t1")))
        asyncio.run(repo.create(_make_template(template_id="t2", name="B")))
        all_t = asyncio.run(repo.list_all(TEST_USER_ID))
        assert len(all_t) == 2

    def test_list_by_status(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.create(_make_template(template_id="t1")))
        t2 = _make_template(template_id="t2", name="B")
        asyncio.run(repo.create(t2.model_copy(update={"status": TemplateStatus.ACTIVE})))
        draft = asyncio.run(repo.list_by_status(TEST_USER_ID, TemplateStatus.DRAFT))
        assert len(draft) == 1

    def test_list_by_category(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.create(_make_template(category="loyalty")))
        asyncio.run(repo.create(_make_template(template_id="t2", name="B", category="reward")))
        loyalty = asyncio.run(repo.list_by_category(TEST_USER_ID, "loyalty"))
        assert len(loyalty) == 1

    def test_list_by_strategy(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.create(_make_template(strategy="retention")))
        asyncio.run(repo.create(_make_template(template_id="t2", name="B", strategy="engagement")))
        retention = asyncio.run(repo.list_by_strategy(TEST_USER_ID, "retention"))
        assert len(retention) == 1

    def test_list_by_token_standard(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.create(_make_template(standard="ERC20")))
        asyncio.run(repo.create(_make_template(template_id="t2", name="B", standard="ERC721")))
        erc20 = asyncio.run(repo.list_by_token_standard(TEST_USER_ID, "ERC20"))
        assert len(erc20) == 1

    def test_search_by_query(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.create(_make_template(name="Loyalty Token", category="loyalty")))
        asyncio.run(repo.create(_make_template(template_id="t2", name="Reward Token", category="reward")))
        results = asyncio.run(repo.search(user_id=TEST_USER_ID, query="loyalty"))
        assert len(results) == 1

    def test_search_by_category(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.create(_make_template(category="loyalty")))
        asyncio.run(repo.create(_make_template(template_id="t2", name="B", category="reward")))
        results = asyncio.run(repo.search(user_id=TEST_USER_ID, category="reward"))
        assert len(results) == 1

    def test_search_by_token_standard(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.create(_make_template(standard="ERC20")))
        asyncio.run(repo.create(_make_template(template_id="t2", name="B", standard="ERC721")))
        results = asyncio.run(repo.search(user_id=TEST_USER_ID, token_standard="ERC721"))
        assert len(results) == 1

    def test_search_by_status(self):
        repo = InMemoryTemplateRepository()
        asyncio.run(repo.create(_make_template()))
        t2 = _make_template(template_id="t2", name="B")
        asyncio.run(repo.create(t2.model_copy(update={"status": TemplateStatus.ACTIVE})))
        results = asyncio.run(repo.search(user_id=TEST_USER_ID, status=TemplateStatus.ACTIVE))
        assert len(results) == 1

    def test_count(self):
        repo = InMemoryTemplateRepository()
        assert asyncio.run(repo.count(TEST_USER_ID)) == 0
        asyncio.run(repo.create(_make_template()))
        assert asyncio.run(repo.count(TEST_USER_ID)) == 1
