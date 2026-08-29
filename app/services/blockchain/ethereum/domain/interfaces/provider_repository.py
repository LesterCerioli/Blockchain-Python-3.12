from abc import ABC, abstractmethod

from ..entities.provider import ProviderRecord


class IProviderRepository(ABC):
    @abstractmethod
    async def get_all(self) -> list[ProviderRecord]: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> ProviderRecord | None: ...

    @abstractmethod
    async def upsert(self, record: ProviderRecord) -> None: ...
