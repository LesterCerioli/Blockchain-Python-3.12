from typing import Any, Callable, Coroutine

from .base_provider import BaseProvider, NodeConfig
from ..rpc.btc_rpc_client import BtcRpcClient


class RpcProvider(BaseProvider):

    def __init__(self, config: NodeConfig) -> None:
        super().__init__(config)
        self._client = BtcRpcClient(
            url=config.url,
            rpc_user=config.rpc_user,
            rpc_password=config.rpc_password,
            timeout_seconds=config.request_timeout,
        )

    async def _guarded(self, coro_func: Callable[[], Coroutine]) -> Any:
        if self._circuit_breaker.is_open():
            raise ConnectionError(
                f"Circuit breaker OPEN for node '{self.name}' — skipping"
            )
        try:
            result = await coro_func()
            self._circuit_breaker.record_success()
            return result
        except Exception:
            self._circuit_breaker.record_failure()
            raise

    async def get_block_height(self) -> int:
        return await self._guarded(self._client.get_block_count)

    async def get_network(self) -> str:
        return await self._guarded(self._client.get_network)

    async def is_syncing(self) -> bool:
        return await self._guarded(self._client.is_syncing)

    async def close(self) -> None:
        await self._client.close()
