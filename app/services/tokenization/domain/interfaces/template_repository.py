from abc import ABC, abstractmethod

from ..entities.template import Template
from ..entities.template_status import TemplateStatus


class ITemplateRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: str, template_id: str) -> Template | None: ...

    @abstractmethod
    async def get_by_name(self, user_id: str, name: str) -> Template | None: ...

    @abstractmethod
    async def create(self, template: Template) -> None: ...

    @abstractmethod
    async def update(self, template: Template) -> None: ...

    @abstractmethod
    async def delete(self, user_id: str, template_id: str) -> None: ...

    @abstractmethod
    async def list_all(self, user_id: str) -> list[Template]: ...

    @abstractmethod
    async def list_by_status(self, user_id: str, status: TemplateStatus) -> list[Template]: ...

    @abstractmethod
    async def list_by_category(self, user_id: str, category: str) -> list[Template]: ...

    @abstractmethod
    async def list_by_strategy(self, user_id: str, strategy: str) -> list[Template]: ...

    @abstractmethod
    async def list_by_token_standard(self, user_id: str, standard: str) -> list[Template]: ...

    @abstractmethod
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
    ) -> list[Template]: ...

    @abstractmethod
    async def count(self, user_id: str) -> int: ...
