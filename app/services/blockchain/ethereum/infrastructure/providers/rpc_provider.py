from typing import Any, Callable, Coroutine

from .base_provider import BaseProvider, ProviderConfig
from ..rpc.eth_rpc_client import EthRpcClient


class RpcProvider(BaseProvider):
    
    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._client = EthRpcClient(config.url, config.request_timeout)

    async def _guarded(self, coro_func: Callable[[], Coroutine]) -> Any:
        if self._circuit_breaker.is_open():
            raise ConnectionError(
                f"Circuit breaker OPEN for provider '{self.name}' — skipping"
            )
        try:
            result = await coro_func()
            self._circuit_breaker.record_success()
            return result
        except Exception:
            self._circuit_breaker.record_failure()
            raise

    async def get_block_number(self) -> int:
        return await self._guarded(self._client.eth_block_number)

    async def get_chain_id(self) -> int:
        return await self._guarded(self._client.eth_chain_id)

    async def is_syncing(self) -> bool:
        return await self._guarded(self._client.eth_syncing)

    async def close(self) -> None:
        await self._client.close()
