from abc import ABC, abstractmethod
from typing import Optional

from ..entities.node import NodeRecord


class INodeRepository(ABC):

    @abstractmethod
    async def get_all(self) -> list[NodeRecord]: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[NodeRecord]: ...

    @abstractmethod
    async def upsert(self, record: NodeRecord) -> None: ...
