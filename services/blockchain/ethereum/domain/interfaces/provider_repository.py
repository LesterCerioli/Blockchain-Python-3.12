from abc import ABC, abstractmethod
from typing import Optional

from ..entities.provider import ProviderRecord


class IProviderRepository(ABC):
    """Port: persistence contract for Ethereum provider state."""

    @abstractmethod
    async def get_all(self) -> list[ProviderRecord]: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[ProviderRecord]: ...

    @abstractmethod
    async def upsert(self, record: ProviderRecord) -> None: ...
