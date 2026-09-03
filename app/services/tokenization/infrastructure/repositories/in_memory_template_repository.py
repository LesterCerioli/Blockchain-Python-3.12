from app.services.tokenization.domain.entities.template import Template
from app.services.tokenization.domain.entities.template_status import TemplateStatus
from app.services.tokenization.domain.interfaces.template_repository import ITemplateRepository
from app.services.tokenization.infrastructure.seed_data import SEED_TEMPLATES


class InMemoryTemplateRepository(ITemplateRepository):
    """In-memory template repository pre-loaded with seed data for journey service."""

    def __init__(self) -> None:
        self._store: dict[str, Template] = {}
        self._load_seed_data()

    def _load_seed_data(self) -> None:
        for template in SEED_TEMPLATES:
            self._store[template.template_id] = template

    async def get_by_id(self, user_id: str, template_id: str) -> Template | None:
        return self._store.get(template_id)

    async def get_by_name(self, user_id: str, name: str) -> Template | None:
        for template in self._store.values():
            if template.name.lower() == name.lower():
                return template
        return None

    async def create(self, template: Template) -> None:
        self._store[template.template_id] = template

    async def update(self, template: Template) -> None:
        self._store[template.template_id] = template

    async def delete(self, user_id: str, template_id: str) -> None:
        self._store.pop(template_id, None)

    async def list_all(self, user_id: str) -> list[Template]:
        return list(self._store.values())

    async def list_by_status(self, user_id: str, status: TemplateStatus) -> list[Template]:
        return [t for t in self._store.values() if t.status == status]

    async def list_by_category(self, user_id: str, category: str) -> list[Template]:
        return [
            t for t in self._store.values()
            if t.category.lower() == category.lower()
        ]

    async def list_by_strategy(self, user_id: str, strategy: str) -> list[Template]:
        return [
            t for t in self._store.values()
            if t.strategy.lower() == strategy.lower()
        ]

    async def list_by_token_standard(self, user_id: str, standard: str) -> list[Template]:
        return [
            t for t in self._store.values()
            if t.token_standard.upper() == standard.upper()
        ]

    async def search(
        self,
        user_id: str,
        query: str | None = None,
        category: str | None = None,
        strategy: str | None = None,
        token_standard: str | None = None,
        status: TemplateStatus | None = None,
        tags: list[str] | None = None,
        industry: str | None = None,
    ) -> list[Template]:
        results = list(self._store.values())

        if query is not None:
            q = query.lower()
            results = [
                t for t in results
                if q in t.name.lower()
                or q in t.description.lower()
                or q in t.category.lower()
                or q in t.strategy.lower()
            ]

        if category is not None:
            results = [
                t for t in results
                if t.category.lower() == category.lower()
            ]

        if strategy is not None:
            results = [
                t for t in results
                if t.strategy.lower() == strategy.lower()
            ]

        if token_standard is not None:
            results = [
                t for t in results
                if t.token_standard.upper() == token_standard.upper()
            ]

        if status is not None:
            results = [t for t in results if t.status == status]

        if tags is not None:
            tag_set = {tag.lower() for tag in tags}
            results = [
                t for t in results
                if tag_set & {tag.lower() for tag in t.metadata.tags}
            ]

        if industry is not None:
            results = [
                t for t in results
                if t.characteristics.industry.lower() == industry.lower()
            ]

        return results

    async def count(self, user_id: str) -> int:
        return len(self._store)
