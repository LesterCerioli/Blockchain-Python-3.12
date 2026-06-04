import json
from decimal import Decimal

import httpx
import pytest
import respx

from app.services.defi.domain.exceptions import ProviderUnavailableError, RateLimitError
from app.services.defi.infrastructure.market_data.coingecko_adapter import (
    CoinGeckoAdapter,
    SYMBOL_TO_COIN_ID,
)

BASE_URL = "https://api.coingecko.com/api/v3"

SIMPLE_PRICE_RESPONSE = {
    "bitcoin": {"usd": 65000.0, "usd_24h_change": 1.5},
    "ethereum": {"usd": 3500.0, "usd_24h_change": -0.8},
    "solana": {"usd": 150.0, "usd_24h_change": 2.1},
}

OHLCV_RESPONSE = [
    [1717200000000, 64000.0, 66000.0, 63500.0, 65000.0],
    [1717203600000, 65000.0, 65500.0, 64800.0, 65200.0],
]


@pytest.fixture
def http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient()


@pytest.mark.asyncio
async def test_symbol_mappings_btc_eth_sol() -> None:
    assert SYMBOL_TO_COIN_ID["BTC"] == "bitcoin"
    assert SYMBOL_TO_COIN_ID["ETH"] == "ethereum"
    assert SYMBOL_TO_COIN_ID["SOL"] == "solana"


@pytest.mark.asyncio
@respx.mock
async def test_get_quote_btc(http_client: httpx.AsyncClient) -> None:
    respx.get(f"{BASE_URL}/simple/price").mock(
        return_value=httpx.Response(
            200, json={"bitcoin": {"usd": 65000.0, "usd_24h_change": 1.5}}
        )
    )
    adapter = CoinGeckoAdapter(http_client, base_url=BASE_URL)
    quote = await adapter.get_quote("BTC")

    assert quote.symbol == "BTC"
    assert quote.vs_currency == "usd"
    assert quote.price == Decimal("65000.0")
    assert quote.price_change_24h == Decimal("1.5")


@pytest.mark.asyncio
@respx.mock
async def test_get_quote_eth(http_client: httpx.AsyncClient) -> None:
    respx.get(f"{BASE_URL}/simple/price").mock(
        return_value=httpx.Response(
            200, json={"ethereum": {"usd": 3500.0, "usd_24h_change": -0.8}}
        )
    )
    adapter = CoinGeckoAdapter(http_client, base_url=BASE_URL)
    quote = await adapter.get_quote("ETH")

    assert quote.symbol == "ETH"
    assert quote.price == Decimal("3500.0")


@pytest.mark.asyncio
@respx.mock
async def test_get_quote_sol(http_client: httpx.AsyncClient) -> None:
    respx.get(f"{BASE_URL}/simple/price").mock(
        return_value=httpx.Response(
            200, json={"solana": {"usd": 150.0, "usd_24h_change": 2.1}}
        )
    )
    adapter = CoinGeckoAdapter(http_client, base_url=BASE_URL)
    quote = await adapter.get_quote("SOL")

    assert quote.symbol == "SOL"
    assert quote.price == Decimal("150.0")


@pytest.mark.asyncio
@respx.mock
async def test_get_quotes_multiple(http_client: httpx.AsyncClient) -> None:
    respx.get(f"{BASE_URL}/simple/price").mock(
        return_value=httpx.Response(200, json=SIMPLE_PRICE_RESPONSE)
    )
    adapter = CoinGeckoAdapter(http_client, base_url=BASE_URL)
    quotes = await adapter.get_quotes(["BTC", "ETH", "SOL"])

    assert len(quotes) == 3
    symbols = {q.symbol for q in quotes}
    assert symbols == {"BTC", "ETH", "SOL"}


@pytest.mark.asyncio
@respx.mock
async def test_get_ohlcv(http_client: httpx.AsyncClient) -> None:
    respx.get(f"{BASE_URL}/coins/bitcoin/ohlc").mock(
        return_value=httpx.Response(200, json=OHLCV_RESPONSE)
    )
    adapter = CoinGeckoAdapter(http_client, base_url=BASE_URL)
    candles = await adapter.get_ohlcv("BTC", days=1)

    assert len(candles) == 2
    first = candles[0]
    assert first.open == Decimal("64000.0")
    assert first.high == Decimal("66000.0")
    assert first.low == Decimal("63500.0")
    assert first.close == Decimal("65000.0")


@pytest.mark.asyncio
@respx.mock
async def test_rate_limit_error_on_429(http_client: httpx.AsyncClient) -> None:
    respx.get(f"{BASE_URL}/simple/price").mock(
        return_value=httpx.Response(429, text="Too Many Requests")
    )
    adapter = CoinGeckoAdapter(http_client, base_url=BASE_URL)

    with pytest.raises(RateLimitError) as exc_info:
        await adapter.get_quote("BTC")

    assert exc_info.value.provider == "CoinGecko"


@pytest.mark.asyncio
@respx.mock
async def test_provider_unavailable_on_500(http_client: httpx.AsyncClient) -> None:
    respx.get(f"{BASE_URL}/simple/price").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    adapter = CoinGeckoAdapter(http_client, base_url=BASE_URL)

    with pytest.raises(ProviderUnavailableError) as exc_info:
        await adapter.get_quote("BTC")

    assert exc_info.value.status_code == 500
    assert exc_info.value.provider == "CoinGecko"


@pytest.mark.asyncio
@respx.mock
async def test_provider_unavailable_on_503(http_client: httpx.AsyncClient) -> None:
    respx.get(f"{BASE_URL}/simple/price").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    adapter = CoinGeckoAdapter(http_client, base_url=BASE_URL)

    with pytest.raises(ProviderUnavailableError) as exc_info:
        await adapter.get_quote("ETH")

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
@respx.mock
async def test_rate_limit_on_get_ohlcv_429(http_client: httpx.AsyncClient) -> None:
    respx.get(f"{BASE_URL}/coins/bitcoin/ohlc").mock(
        return_value=httpx.Response(429, text="Too Many Requests")
    )
    adapter = CoinGeckoAdapter(http_client, base_url=BASE_URL)

    with pytest.raises(RateLimitError):
        await adapter.get_ohlcv("BTC")


@pytest.mark.asyncio
@respx.mock
async def test_get_quote_no_24h_change(http_client: httpx.AsyncClient) -> None:
    respx.get(f"{BASE_URL}/simple/price").mock(
        return_value=httpx.Response(200, json={"bitcoin": {"usd": 65000.0}})
    )
    adapter = CoinGeckoAdapter(http_client, base_url=BASE_URL)
    quote = await adapter.get_quote("BTC")

    assert quote.price_change_24h is None


@pytest.mark.asyncio
@respx.mock
async def test_get_quotes_skips_missing_coin(http_client: httpx.AsyncClient) -> None:
    respx.get(f"{BASE_URL}/simple/price").mock(
        return_value=httpx.Response(
            200, json={"bitcoin": {"usd": 65000.0, "usd_24h_change": 1.0}}
        )
    )
    adapter = CoinGeckoAdapter(http_client, base_url=BASE_URL)
    quotes = await adapter.get_quotes(["BTC", "UNKNOWN"])

    assert len(quotes) == 1
    assert quotes[0].symbol == "BTC"
