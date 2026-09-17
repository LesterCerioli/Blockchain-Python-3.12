from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock

import httpx
import pytest
import respx
from tenacity import wait_none

from app.services.defi.domain.exceptions import ProviderUnavailableError, RateLimitError
from app.services.defi.infrastructure.market_data.cmc_adapter import CoinMarketCapAdapter

_BASE_URL = "https://pro-api.coinmarketcap.com/v1"
_API_KEY = "test-api-key"
_QUOTES_URL = f"{_BASE_URL}/cryptocurrency/quotes/latest"
_OHLCV_URL = f"{_BASE_URL}/cryptocurrency/ohlcv/latest"


def _quote_body(
    symbol: str,
    price: float = 65000.0,
    change_24h: float | None = 1.5,
    vs: str = "USD",
) -> dict:
    quote_data: dict = {"price": price, "percent_change_24h": change_24h}
    return {"data": {symbol: {"quote": {vs: quote_data}}}}


def _multi_quote_body(*entries: tuple[str, float], vs: str = "USD") -> dict:
    data = {
        sym: {"quote": {vs: {"price": price, "percent_change_24h": 1.0}}}
        for sym, price in entries
    }
    return {"data": data}


def _ohlcv_body(symbol: str, vs: str = "USD") -> dict:
    return {
        "data": {
            symbol: {
                "quote": {
                    vs: {
                        "open": 64000.0,
                        "high": 66000.0,
                        "low": 63000.0,
                        "close": 65000.0,
                    }
                }
            }
        }
    }


@pytest.fixture
def client() -> httpx.AsyncClient:
    return httpx.AsyncClient()


@pytest.fixture
def adapter(client: httpx.AsyncClient) -> CoinMarketCapAdapter:
    return CoinMarketCapAdapter(
        client, api_key=_API_KEY, base_url=_BASE_URL, retry_wait=wait_none()
    )


# ---------------------------------------------------------------------------
# get_quote — happy paths
# ---------------------------------------------------------------------------


@respx.mock
async def test_get_quote_btc(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(200, json=_quote_body("BTC"))
    )
    quote = await adapter.get_quote("BTC")

    assert quote.symbol == "BTC"
    assert quote.vs_currency == "usd"
    assert quote.price == Decimal("65000.0")
    assert quote.price_change_24h == Decimal("1.5")


@respx.mock
async def test_get_quote_eth(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(
            200, json=_quote_body("ETH", price=3500.0, change_24h=-0.8)
        )
    )
    quote = await adapter.get_quote("ETH")

    assert quote.symbol == "ETH"
    assert quote.price == Decimal("3500.0")
    assert quote.price_change_24h == Decimal("-0.8")


@respx.mock
async def test_get_quote_sol(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(200, json=_quote_body("SOL", price=150.0, change_24h=2.1))
    )
    quote = await adapter.get_quote("SOL")

    assert quote.symbol == "SOL"
    assert quote.price == Decimal("150.0")


@respx.mock
async def test_get_quote_no_24h_change(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(200, json=_quote_body("BTC", change_24h=None))
    )
    quote = await adapter.get_quote("BTC")

    assert quote.price_change_24h is None


@respx.mock
async def test_get_quote_symbol_uppercased(client: httpx.AsyncClient) -> None:
    route = respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(200, json=_quote_body("BTC"))
    )
    adapter = CoinMarketCapAdapter(
        client, api_key=_API_KEY, base_url=_BASE_URL, retry_wait=wait_none()
    )
    quote = await adapter.get_quote("btc")

    assert quote.symbol == "BTC"
    assert "symbol=BTC" in str(route.calls.last.request.url)


@respx.mock
async def test_get_quote_sends_api_key_header(client: httpx.AsyncClient) -> None:
    secret_key = "super-secret-key"
    route = respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(200, json=_quote_body("BTC"))
    )
    adapter = CoinMarketCapAdapter(
        client, api_key=secret_key, base_url=_BASE_URL, retry_wait=wait_none()
    )
    await adapter.get_quote("BTC")

    assert route.calls.last.request.headers["X-CMC_PRO_API_KEY"] == secret_key


# ---------------------------------------------------------------------------
# get_quote — error handling
# ---------------------------------------------------------------------------


@respx.mock
async def test_get_quote_rate_limit_on_429(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(429, text="Too Many Requests")
    )

    with pytest.raises(RateLimitError) as exc_info:
        await adapter.get_quote("BTC")

    assert exc_info.value.provider == "CoinMarketCap"


@respx.mock
async def test_get_quote_rate_limit_includes_retry_after_header(
    adapter: CoinMarketCapAdapter,
) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(
            429, headers={"Retry-After": "30"}, text="Too Many Requests"
        )
    )

    with pytest.raises(RateLimitError) as exc_info:
        await adapter.get_quote("BTC")

    assert exc_info.value.retry_after == 30


@respx.mock
async def test_get_quote_rate_limit_no_retry_after_gives_none(
    adapter: CoinMarketCapAdapter,
) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(429, text="Too Many Requests")
    )

    with pytest.raises(RateLimitError) as exc_info:
        await adapter.get_quote("BTC")

    assert exc_info.value.retry_after is None


@respx.mock
async def test_get_quote_provider_unavailable_on_500(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    with pytest.raises(ProviderUnavailableError) as exc_info:
        await adapter.get_quote("BTC")

    assert exc_info.value.provider == "CoinMarketCap"
    assert exc_info.value.status_code == 500


@respx.mock
async def test_get_quote_provider_unavailable_on_503(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )

    with pytest.raises(ProviderUnavailableError) as exc_info:
        await adapter.get_quote("BTC")

    assert exc_info.value.status_code == 503


# ---------------------------------------------------------------------------
# get_quotes — happy paths
# ---------------------------------------------------------------------------


@respx.mock
async def test_get_quotes_multiple_symbols(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(
            200,
            json=_multi_quote_body(("BTC", 65000.0), ("ETH", 3500.0), ("SOL", 150.0)),
        )
    )
    quotes = await adapter.get_quotes(["BTC", "ETH", "SOL"])

    assert len(quotes) == 3
    symbols = {q.symbol for q in quotes}
    assert symbols == {"BTC", "ETH", "SOL"}


@respx.mock
async def test_get_quotes_correct_prices(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(
            200, json=_multi_quote_body(("BTC", 65000.0), ("ETH", 3500.0))
        )
    )
    quotes = await adapter.get_quotes(["BTC", "ETH"])
    price_map = {q.symbol: q.price for q in quotes}

    assert price_map["BTC"] == Decimal("65000.0")
    assert price_map["ETH"] == Decimal("3500.0")


@respx.mock
async def test_get_quotes_no_24h_change(adapter: CoinMarketCapAdapter) -> None:
    body = {
        "data": {
            "BTC": {"quote": {"USD": {"price": 65000.0, "percent_change_24h": None}}}
        }
    }
    respx.get(_QUOTES_URL).mock(return_value=httpx.Response(200, json=body))
    quotes = await adapter.get_quotes(["BTC"])

    assert quotes[0].price_change_24h is None


@respx.mock
async def test_get_quotes_vs_currency_lowercased(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(200, json=_multi_quote_body(("BTC", 65000.0)))
    )
    quotes = await adapter.get_quotes(["BTC"])

    assert quotes[0].vs_currency == "usd"


# ---------------------------------------------------------------------------
# get_quotes — error handling
# ---------------------------------------------------------------------------


@respx.mock
async def test_get_quotes_rate_limit_on_429(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(429, text="Too Many Requests")
    )

    with pytest.raises(RateLimitError):
        await adapter.get_quotes(["BTC", "ETH"])


@respx.mock
async def test_get_quotes_provider_unavailable_on_500(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_QUOTES_URL).mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    with pytest.raises(ProviderUnavailableError):
        await adapter.get_quotes(["BTC"])


# ---------------------------------------------------------------------------
# get_ohlcv — happy paths
# ---------------------------------------------------------------------------


@respx.mock
async def test_get_ohlcv_returns_one_candle(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_OHLCV_URL).mock(
        return_value=httpx.Response(200, json=_ohlcv_body("BTC"))
    )
    candles = await adapter.get_ohlcv("BTC")

    assert len(candles) == 1


@respx.mock
async def test_get_ohlcv_correct_values(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_OHLCV_URL).mock(
        return_value=httpx.Response(200, json=_ohlcv_body("BTC"))
    )
    candles = await adapter.get_ohlcv("BTC")
    candle = candles[0]

    assert candle.open == Decimal("64000.0")
    assert candle.high == Decimal("66000.0")
    assert candle.low == Decimal("63000.0")
    assert candle.close == Decimal("65000.0")


@respx.mock
async def test_get_ohlcv_eth(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_OHLCV_URL).mock(
        return_value=httpx.Response(200, json=_ohlcv_body("ETH"))
    )
    candles = await adapter.get_ohlcv("ETH")

    assert len(candles) == 1
    assert candles[0].open == Decimal("64000.0")


# ---------------------------------------------------------------------------
# get_ohlcv — error handling
# ---------------------------------------------------------------------------


@respx.mock
async def test_get_ohlcv_rate_limit_on_429(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_OHLCV_URL).mock(
        return_value=httpx.Response(429, text="Too Many Requests")
    )

    with pytest.raises(RateLimitError):
        await adapter.get_ohlcv("BTC")


@respx.mock
async def test_get_ohlcv_provider_unavailable_on_500(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_OHLCV_URL).mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    with pytest.raises(ProviderUnavailableError):
        await adapter.get_ohlcv("BTC")


@respx.mock
async def test_get_ohlcv_provider_unavailable_on_503(adapter: CoinMarketCapAdapter) -> None:
    respx.get(_OHLCV_URL).mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )

    with pytest.raises(ProviderUnavailableError):
        await adapter.get_ohlcv("BTC")


# ---------------------------------------------------------------------------
# rate_limiter integration
# ---------------------------------------------------------------------------


async def test_get_quote_rate_limiter_checked(client: httpx.AsyncClient) -> None:
    rate_limiter = AsyncMock()
    adapter = CoinMarketCapAdapter(
        client,
        api_key=_API_KEY,
        base_url=_BASE_URL,
        rate_limiter=rate_limiter,
        retry_wait=wait_none(),
    )

    with respx.mock:
        respx.get(_QUOTES_URL).mock(
            return_value=httpx.Response(200, json=_quote_body("BTC"))
        )
        await adapter.get_quote("BTC")

    rate_limiter.check_and_increment.assert_awaited_once()


async def test_get_quotes_rate_limiter_checked(client: httpx.AsyncClient) -> None:
    rate_limiter = AsyncMock()
    adapter = CoinMarketCapAdapter(
        client,
        api_key=_API_KEY,
        base_url=_BASE_URL,
        rate_limiter=rate_limiter,
        retry_wait=wait_none(),
    )

    with respx.mock:
        respx.get(_QUOTES_URL).mock(
            return_value=httpx.Response(200, json=_multi_quote_body(("BTC", 65000.0)))
        )
        await adapter.get_quotes(["BTC"])

    rate_limiter.check_and_increment.assert_awaited_once()


async def test_get_ohlcv_rate_limiter_checked(client: httpx.AsyncClient) -> None:
    rate_limiter = AsyncMock()
    adapter = CoinMarketCapAdapter(
        client,
        api_key=_API_KEY,
        base_url=_BASE_URL,
        rate_limiter=rate_limiter,
        retry_wait=wait_none(),
    )

    with respx.mock:
        respx.get(_OHLCV_URL).mock(
            return_value=httpx.Response(200, json=_ohlcv_body("BTC"))
        )
        await adapter.get_ohlcv("BTC")

    rate_limiter.check_and_increment.assert_awaited_once()
