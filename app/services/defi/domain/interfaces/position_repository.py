import uuid
from abc import ABC, abstractmethod

from ..entities.position import Position


class IPositionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, position_id: uuid.UUID) -> Position | None: ...

    @abstractmethod
    async def list_by_owner(self, owner: str, chain_id: int) -> list[Position]: ...

    @abstractmethod
    async def upsert(self, position: Position) -> None: ...

    @abstractmethod
    async def delete(self, position_id: uuid.UUID) -> None: ...
