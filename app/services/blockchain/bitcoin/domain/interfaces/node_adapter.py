from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class BlockInfo:
    height: int
    hash: str
    timestamp: int


class IBitcoinNodeAdapter(ABC):

    @abstractmethod
    async def get_block_height(self) -> int: ...

    @abstractmethod
    async def get_network(self) -> str: ...

    @abstractmethod
    async def is_syncing(self) -> bool: ...
