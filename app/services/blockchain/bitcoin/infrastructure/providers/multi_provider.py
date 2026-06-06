from typing import Any, Callable, Coroutine

from .base_provider import BaseProvider


class MultiProvider:

    def __init__(self, providers: list[BaseProvider]) -> None:
        self._providers = sorted(providers, key=lambda p: p.priority)

    @property
    def providers(self) -> list[BaseProvider]:
        return list(self._providers)

    def _available(self) -> list[BaseProvider]:
        return [p for p in self._providers if p.is_available]

    async def _call_with_failover(self, method: str, *args: Any, **kwargs: Any) -> Any:
        available = self._available()
        if not available:
            raise RuntimeError("No Bitcoin nodes available (all circuit-breakers open)")

        last_exc: Exception = RuntimeError("No nodes tried")
        for provider in available:
            try:
                return await getattr(provider, method)(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                continue

        raise RuntimeError(
            f"All {len(available)} node(s) failed. Last error: {last_exc}"
        ) from last_exc

    async def get_block_height(self) -> int:
        return await self._call_with_failover("get_block_height")

    async def get_network(self) -> str:
        return await self._call_with_failover("get_network")

    async def is_syncing(self) -> bool:
        return await self._call_with_failover("is_syncing")

    async def close(self) -> None:
        for provider in self._providers:
            await provider.close()
