from abc import ABC, abstractmethod
from typing import Optional

from ..entities.pool import Pool


class IPoolRepository(ABC):

    @abstractmethod
    async def get_by_address(self, address: str) -> Optional[Pool]: ...

    @abstractmethod
    async def list_by_tokens(self, token0: str, token1: str, chain_id: int) -> list[Pool]: ...

    @abstractmethod
    async def list_by_protocol(self, protocol: str, chain_id: int) -> list[Pool]: ...

    @abstractmethod
    async def list_by_chain(
        self,
        chain_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Pool]: ...

    @abstractmethod
    async def upsert(self, pool: Pool) -> None: ...

    @abstractmethod
    async def delete(self, address: str) -> None: ...

    @abstractmethod
    async def count_by_chain(self, chain_id: int) -> int: ...
