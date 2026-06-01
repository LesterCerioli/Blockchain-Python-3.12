from typing import Optional

from ...domain.entities.provider import ProviderRecord
from ...domain.interfaces.provider_repository import IProviderRepository


class InMemoryProviderRepository(IProviderRepository):
    
    def __init__(self) -> None:
        self._store: dict[str, ProviderRecord] = {}

    async def get_all(self) -> list[ProviderRecord]:
        return list(self._store.values())

    async def get_by_name(self, name: str) -> Optional[ProviderRecord]:
        return self._store.get(name)

    async def upsert(self, record: ProviderRecord) -> None:
        self._store[record.name] = record
