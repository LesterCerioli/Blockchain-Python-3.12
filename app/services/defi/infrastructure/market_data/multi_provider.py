from typing import Any

from ...domain.exceptions import ProviderUnavailableError, RateLimitError
from ...domain.value_objects.market_quote import MarketQuote
from ...domain.value_objects.ohlcv_candle import OHLCVCandle
from .circuit_breaker import CircuitBreaker

_FAILURE_THRESHOLD = 3
_RECOVERY_TIMEOUT_SECONDS = 30
_FAILOVER_ERRORS = (ProviderUnavailableError, RateLimitError)


class MultiMarketDataProvider:

    def __init__(self, providers: list[Any]) -> None:
        self._entries: list[tuple[Any, CircuitBreaker]] = [
            (
                p,
                CircuitBreaker(
                    name=type(p).__name__,
                    failure_threshold=_FAILURE_THRESHOLD,
                    recovery_timeout_seconds=_RECOVERY_TIMEOUT_SECONDS,
                ),
            )
            for p in providers
        ]

    @property
    def providers(self) -> list[Any]:
        return [p for p, _ in self._entries]

    def _available(self) -> list[tuple[Any, CircuitBreaker]]:
        return [(p, cb) for p, cb in self._entries if not cb.is_open()]

    async def _call_with_failover(self, method: str, *args: Any, **kwargs: Any) -> Any:
        available = self._available()
        if not available:
            raise RuntimeError(
                "No market data providers available (all circuit-breakers open)"
            )
        last_exc: Exception = RuntimeError("No providers tried")
        for provider, breaker in available:
            try:
                result = await getattr(provider, method)(*args, **kwargs)
                breaker.record_success()
                return result
            except _FAILOVER_ERRORS as exc:
                breaker.record_failure()
                last_exc = exc
        raise RuntimeError(
            f"All {len(available)} provider(s) failed. Last error: {last_exc}"
        ) from last_exc

    async def get_quote(self, symbol: str, vs_currency: str = "usd") -> MarketQuote:
        return await self._call_with_failover("get_quote", symbol, vs_currency)

    async def get_quotes(
        self, symbols: list[str], vs_currency: str = "usd"
    ) -> list[MarketQuote]:
        return await self._call_with_failover("get_quotes", symbols, vs_currency)

    async def get_ohlcv(
        self, symbol: str, vs_currency: str = "usd", days: int = 1
    ) -> list[OHLCVCandle]:
        return await self._call_with_failover("get_ohlcv", symbol, vs_currency, days)
