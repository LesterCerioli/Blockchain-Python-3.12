from ..interfaces.node_adapter import IBitcoinNodeAdapter


class BtcNodeAdapter(IBitcoinNodeAdapter):

    def __init__(self, provider: "MultiProvider") -> None:  # type: ignore[name-defined]
        self._provider = provider

    async def get_block_height(self) -> int:
        return await self._provider.get_block_height()

    async def get_network(self) -> str:
        return await self._provider.get_network()

    async def is_syncing(self) -> bool:
        return await self._provider.is_syncing()
