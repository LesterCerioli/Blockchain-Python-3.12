from abc import ABC, abstractmethod
from typing import Optional

from ..entities.token import Token


class ITokenRepository(ABC):

    @abstractmethod
    async def get_by_address(self, address: str, chain_id: int) -> Optional[Token]: ...

    @abstractmethod
    async def get_batch(self, addresses: list[str], chain_id: int) -> list[Token]:
        """Returns all tokens matching the given addresses on a single chain."""
        ...

    @abstractmethod
    async def search_by_symbol(self, symbol: str, chain_id: int) -> list[Token]:
        """Case-insensitive prefix search on token symbol."""
        ...

    @abstractmethod
    async def list_by_chain(self, chain_id: int) -> list[Token]: ...

    @abstractmethod
    async def upsert(self, token: Token) -> None: ...

    @abstractmethod
    async def delete(self, address: str, chain_id: int) -> None: ...

    @abstractmethod
    async def count_by_chain(self, chain_id: int) -> int: ...
