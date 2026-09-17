from abc import ABC, abstractmethod

from ..entities.token import Token


class ITokenRepository(ABC):
    @abstractmethod
    async def get_by_address(self, address: str, chain_id: int) -> Token | None: ...

    @abstractmethod
    async def list_by_chain(self, chain_id: int) -> list[Token]: ...

    @abstractmethod
    async def upsert(self, token: Token) -> None: ...
