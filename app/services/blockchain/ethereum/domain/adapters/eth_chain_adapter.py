from __future__ import annotations

from typing import TYPE_CHECKING

from ..interfaces.chain_adapter import IChainAdapter

if TYPE_CHECKING:
    from ...infrastructure.providers.multi_provider import MultiProvider


class EthChainAdapter(IChainAdapter):
    def __init__(self, provider: MultiProvider) -> None:
        self._provider = provider

    async def get_block_number(self) -> int:
        return await self._provider.get_block_number()

    async def get_chain_id(self) -> int:
        return await self._provider.get_chain_id()

    async def is_syncing(self) -> bool:
        return await self._provider.is_syncing()
