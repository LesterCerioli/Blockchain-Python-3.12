from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class BlockInfo:
    number: int
    hash: str
    timestamp: int


class IChainAdapter(ABC):
    """Port: contract for reading on-chain state, chain-agnostic."""

    @abstractmethod
    async def get_block_number(self) -> int: ...

    @abstractmethod
    async def get_chain_id(self) -> int: ...

    @abstractmethod
    async def is_syncing(self) -> bool: ...
