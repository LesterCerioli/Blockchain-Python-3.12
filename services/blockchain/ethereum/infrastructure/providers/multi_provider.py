from typing import Any, Callable, Coroutine

from .base_provider import BaseProvider


class MultiProvider:
    """
    Manages a priority-ordered list of providers with automatic failover.
    Requests are forwarded to the highest-priority available provider;
    on failure it transparently tries the next one (SRP: only failover logic).
    """

    def __init__(self, providers: list[BaseProvider]) -> None:
        # Sort ascending by priority so index-0 is tried first
        self._providers = sorted(providers, key=lambda p: p.priority)

    @property
    def providers(self) -> list[BaseProvider]:
        return list(self._providers)

    def _available(self) -> list[BaseProvider]:
        return [p for p in self._providers if p.is_available]

    async def _call_with_failover(
        self,
        method: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        available = self._available()
        if not available:
            raise RuntimeError("No Ethereum providers available (all circuit-breakers open)")

        last_exc: Exception = RuntimeError("No providers tried")
        for provider in available:
            try:
                return await getattr(provider, method)(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                continue

        raise RuntimeError(
            f"All {len(available)} provider(s) failed. Last error: {last_exc}"
        ) from last_exc

    async def get_block_number(self) -> int:
        return await self._call_with_failover("get_block_number")

    async def get_chain_id(self) -> int:
        return await self._call_with_failover("get_chain_id")

    async def is_syncing(self) -> bool:
        return await self._call_with_failover("is_syncing")

    async def close(self) -> None:
        for provider in self._providers:
            await provider.close()
