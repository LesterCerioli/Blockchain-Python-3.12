import sys
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.services.defi.domain.exceptions import ProviderUnavailableError, RateLimitError
from app.services.defi.domain.value_objects.market_quote import MarketQuote
from app.services.defi.domain.value_objects.ohlcv_candle import OHLCVCandle
from app.services.defi.infrastructure.market_data.circuit_breaker import CircuitBreaker, CircuitState
from app.services.defi.infrastructure.market_data.multi_provider import MultiMarketDataProvider


def _make_quote(symbol: str = "BTC", price: float = 65000.0) -> MarketQuote:
    return MarketQuote(
        symbol=symbol,
        vs_currency="usd",
        price=Decimal(str(price)),
        price_change_24h=None,
        timestamp=datetime.now(tz=timezone.utc),
    )


def _make_candle() -> OHLCVCandle:
    return OHLCVCandle(
        timestamp=datetime.now(tz=timezone.utc),
        open=Decimal("64000"),
        high=Decimal("66000"),
        low=Decimal("63000"),
        close=Decimal("65000"),
    )


def _make_provider(name: str, quote: MarketQuote | None = None, error: Exception | None = None):
    p = MagicMock()
    p.__class__.__name__ = name
    if error is not None:
        p.get_quote = AsyncMock(side_effect=error)
        p.get_quotes = AsyncMock(side_effect=error)
        p.get_ohlcv = AsyncMock(side_effect=error)
    else:
        p.get_quote = AsyncMock(return_value=quote or _make_quote())
        p.get_quotes = AsyncMock(return_value=[quote or _make_quote()])
        p.get_ohlcv = AsyncMock(return_value=[_make_candle()])
    return p


# ---------------------------------------------------------------------------
# Failover behaviour
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_primary_succeeds_secondary_not_called() -> None:
    primary = _make_provider("CoinGeckoAdapter")
    secondary = _make_provider("CoinMarketCapAdapter")

    mp = MultiMarketDataProvider([primary, secondary])
    await mp.get_quote("BTC")

    primary.get_quote.assert_awaited_once()
    secondary.get_quote.assert_not_awaited()


@pytest.mark.asyncio
async def test_failover_to_secondary_on_provider_unavailable() -> None:
    expected = _make_quote(price=64000.0)
    primary = _make_provider("CoinGeckoAdapter", error=ProviderUnavailableError("CoinGecko", 503))
    secondary = _make_provider("CoinMarketCapAdapter", quote=expected)

    mp = MultiMarketDataProvider([primary, secondary])
    result = await mp.get_quote("BTC")

    assert result.price == expected.price
    secondary.get_quote.assert_awaited_once()


@pytest.mark.asyncio
async def test_failover_to_secondary_on_rate_limit() -> None:
    expected = _make_quote(price=64500.0)
    primary = _make_provider("CoinGeckoAdapter", error=RateLimitError("CoinGecko"))
    secondary = _make_provider("CoinMarketCapAdapter", quote=expected)

    mp = MultiMarketDataProvider([primary, secondary])
    result = await mp.get_quote("BTC")

    assert result.price == expected.price


@pytest.mark.asyncio
async def test_raises_when_all_providers_fail() -> None:
    p1 = _make_provider("CoinGeckoAdapter", error=ProviderUnavailableError("CoinGecko", 503))
    p2 = _make_provider("CoinMarketCapAdapter", error=RateLimitError("CoinMarketCap"))

    mp = MultiMarketDataProvider([p1, p2])

    with pytest.raises(RuntimeError, match="All.*provider"):
        await mp.get_quote("BTC")


@pytest.mark.asyncio
async def test_get_quotes_failover() -> None:
    expected = [_make_quote("ETH", price=3500.0)]
    primary = _make_provider("CoinGeckoAdapter", error=RateLimitError("CoinGecko"))
    secondary = _make_provider("CoinMarketCapAdapter")
    secondary.get_quotes = AsyncMock(return_value=expected)

    mp = MultiMarketDataProvider([primary, secondary])
    result = await mp.get_quotes(["ETH"])

    assert result == expected


@pytest.mark.asyncio
async def test_get_ohlcv_failover() -> None:
    candle = _make_candle()
    primary = _make_provider("CoinGeckoAdapter", error=ProviderUnavailableError("CoinGecko", 500))
    secondary = _make_provider("CoinMarketCapAdapter")
    secondary.get_ohlcv = AsyncMock(return_value=[candle])

    mp = MultiMarketDataProvider([primary, secondary])
    result = await mp.get_ohlcv("BTC")

    assert result == [candle]


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_3_failures() -> None:
    primary = _make_provider("CoinGeckoAdapter", error=ProviderUnavailableError("CoinGecko", 503))
    secondary = _make_provider("CoinMarketCapAdapter")

    mp = MultiMarketDataProvider([primary, secondary])

    for _ in range(3):
        await mp.get_quote("BTC")

    _, primary_breaker = mp._entries[0]
    assert primary_breaker.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_open_circuit_breaker_skips_provider() -> None:
    primary = _make_provider("CoinGeckoAdapter", error=ProviderUnavailableError("CoinGecko", 503))
    secondary = _make_provider("CoinMarketCapAdapter")

    mp = MultiMarketDataProvider([primary, secondary])

    for _ in range(3):
        await mp.get_quote("BTC")

    primary.get_quote.reset_mock()
    await mp.get_quote("BTC")

    primary.get_quote.assert_not_awaited()
    secondary.get_quote.assert_awaited()


@pytest.mark.asyncio
async def test_circuit_breaker_closes_after_recovery_timeout() -> None:
    error = ProviderUnavailableError("CoinGecko", 503)
    primary = _make_provider("CoinGeckoAdapter", error=error)
    secondary = _make_provider("CoinMarketCapAdapter")

    mp = MultiMarketDataProvider([primary, secondary])

    for _ in range(3):
        await mp.get_quote("BTC")

    _, primary_breaker = mp._entries[0]
    assert primary_breaker.state == CircuitState.OPEN

    # Simulate 30s passing by backdating the last failure time.
    primary_breaker._last_failure_time = datetime.now(tz=timezone.utc) - timedelta(seconds=31)

    assert primary_breaker.state == CircuitState.HALF_OPEN


@pytest.mark.asyncio
async def test_no_providers_available_raises_runtime_error() -> None:
    primary = _make_provider("CoinGeckoAdapter", error=ProviderUnavailableError("CoinGecko", 503))

    mp = MultiMarketDataProvider([primary])
    _, breaker = mp._entries[0]

    for _ in range(3):
        try:
            await mp.get_quote("BTC")
        except RuntimeError:
            pass

    assert breaker.state == CircuitState.OPEN

    with pytest.raises(RuntimeError, match="No market data providers available"):
        await mp.get_quote("BTC")


@pytest.mark.asyncio
async def test_success_resets_circuit_breaker() -> None:
    error = ProviderUnavailableError("CoinGecko", 503)
    primary = _make_provider("CoinGeckoAdapter", error=error)
    secondary = _make_provider("CoinMarketCapAdapter")

    mp = MultiMarketDataProvider([primary, secondary])

    for _ in range(2):
        await mp.get_quote("BTC")

    _, primary_breaker = mp._entries[0]
    assert primary_breaker.state == CircuitState.CLOSED

    primary.get_quote = AsyncMock(return_value=_make_quote())
    primary_breaker._last_failure_time = datetime.now(tz=timezone.utc) - timedelta(seconds=31)
    primary_breaker._state = CircuitState.HALF_OPEN

    await mp.get_quote("BTC")
    assert primary_breaker.state == CircuitState.CLOSED
    assert primary_breaker._failure_count == 0
