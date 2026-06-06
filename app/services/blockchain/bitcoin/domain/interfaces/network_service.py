from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkInfo:
    network: str
    block_height: int
    is_syncing: bool


class INetworkService(ABC):

    @abstractmethod
    async def get_network_info(self) -> NetworkInfo: ...
