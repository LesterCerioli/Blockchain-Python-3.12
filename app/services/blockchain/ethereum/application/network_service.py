from ..domain.entities.chain_config import CHAIN_ID_TO_NETWORK, NetworkName
from ..domain.interfaces.chain_adapter import IChainAdapter
from ..domain.interfaces.network_service import INetworkService, NetworkInfo


class NetworkService(INetworkService):
    
    def __init__(self, chain_adapter: IChainAdapter) -> None:
        self._chain_adapter = chain_adapter

    async def get_network_info(self) -> NetworkInfo:
        chain_id = await self._chain_adapter.get_chain_id()
        is_syncing = await self._chain_adapter.is_syncing()
        network_name = CHAIN_ID_TO_NETWORK.get(chain_id, NetworkName.UNKNOWN)
        return NetworkInfo(
            chain_id=chain_id,
            network_name=network_name.value,
            is_syncing=is_syncing,
        )
