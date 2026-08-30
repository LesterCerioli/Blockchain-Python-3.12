from typing import Optional

from ...domain.entities.node import NodeRecord
from ...domain.interfaces.node_repository import INodeRepository


class InMemoryNodeRepository(INodeRepository):

    def __init__(self) -> None:
        self._store: dict[str, NodeRecord] = {}

    async def get_all(self) -> list[NodeRecord]:
        return list(self._store.values())

    async def get_by_name(self, name: str) -> Optional[NodeRecord]:
        return self._store.get(name)

    async def upsert(self, record: NodeRecord) -> None:
        self._store[record.name] = record
