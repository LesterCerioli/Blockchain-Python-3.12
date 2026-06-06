from ..domain.interfaces.node_adapter import IBitcoinNodeAdapter
from ..domain.interfaces.network_service import INetworkService, NetworkInfo


class NetworkService(INetworkService):

    def __init__(self, node_adapter: IBitcoinNodeAdapter) -> None:
        self._node_adapter = node_adapter

    async def get_network_info(self) -> NetworkInfo:
        network = await self._node_adapter.get_network()
        block_height = await self._node_adapter.get_block_height()
        is_syncing = await self._node_adapter.is_syncing()
        return NetworkInfo(
            network=network,
            block_height=block_height,
            is_syncing=is_syncing,
        )
