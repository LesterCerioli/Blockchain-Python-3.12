from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkInfo:
    chain_id: int
    network_name: str
    is_syncing: bool


class INetworkService(ABC):
    
    @abstractmethod
    async def get_network_info(self) -> NetworkInfo: ...
