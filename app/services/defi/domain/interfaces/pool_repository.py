from abc import ABC, abstractmethod

from ..entities.pool import Pool


class IPoolRepository(ABC):
    @abstractmethod
    async def get_by_address(self, address: str) -> Pool | None: ...

    @abstractmethod
    async def list_by_tokens(
        self, token0: str, token1: str, chain_id: int
    ) -> list[Pool]: ...

    @abstractmethod
    async def upsert(self, pool: Pool) -> None: ...
