from ..interfaces.chain_adapter import IChainAdapter


class EthChainAdapter(IChainAdapter):
    """
    Adapter: translates IChainAdapter calls into MultiProvider calls.
    Satisfies Dependency Inversion — application layer depends on IChainAdapter,
    not on the concrete MultiProvider.
    """

    def __init__(self, provider: "MultiProvider") -> None:  # type: ignore[name-defined]
        self._provider = provider

    async def get_block_number(self) -> int:
        return await self._provider.get_block_number()

    async def get_chain_id(self) -> int:
        return await self._provider.get_chain_id()

    async def is_syncing(self) -> bool:
        return await self._provider.is_syncing()
