from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx
from tenacity import wait_none

from app.services.defi.domain.exceptions import RateLimitError
from app.services.defi.infrastructure.market_data.coingecko_adapter import CoinGeckoAdapter
from app.services.defi.infrastructure.market_data.cmc_adapter import CoinMarketCapAdapter

_CG_BASE = "https://api.coingecko.com/api/v3"
_CMC_BASE = "https://pro-api.coinmarketcap.com/v1"
_API_KEY = "test-key"

_QUOTE_OK = {"bitcoin": {"usd": 65000.0, "usd_24h_change": 1.5}}


@pytest.fixture
def http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient()



@pytest.mark.asyncio
@respx.mock
async def test_coingecko_retries_3_times_on_rate_limit(
    http_client: httpx.AsyncClient,
) -> None:
    respx.get(f"{_CG_BASE}/simple/price").mock(
        return_value=httpx.Response(429, text="Too Many Requests")
    )
    adapter = CoinGeckoAdapter(http_client, base_url=_CG_BASE, retry_wait=wait_none())

    with pytest.raises(RateLimitError):
        await adapter.get_quote("BTC")

    assert respx.calls.call_count == 3


@pytest.mark.asyncio
@respx.mock
async def test_coingecko_succeeds_after_one_retry(
    http_client: httpx.AsyncClient,
) -> None:
    respx.get(f"{_CG_BASE}/simple/price").mock(
        side_effect=[
            httpx.Response(429, text="Too Many Requests"),
            httpx.Response(200, json=_QUOTE_OK),
        ]
    )
    adapter = CoinGeckoAdapter(http_client, base_url=_CG_BASE, retry_wait=wait_none())

    quote = await adapter.get_quote("BTC")

    assert quote.symbol == "BTC"
    assert respx.calls.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_coingecko_ohlcv_retries_on_rate_limit(
    http_client: httpx.AsyncClient,
) -> None:
    respx.get(f"{_CG_BASE}/coins/bitcoin/ohlc").mock(
        return_value=httpx.Response(429, text="Too Many Requests")
    )
    adapter = CoinGeckoAdapter(http_client, base_url=_CG_BASE, retry_wait=wait_none())

    with pytest.raises(RateLimitError):
        await adapter.get_ohlcv("BTC")

    assert respx.calls.call_count == 3


@pytest.mark.asyncio
@respx.mock
async def test_coingecko_no_retry_on_server_error(
    http_client: httpx.AsyncClient,
) -> None:
    from app.services.defi.domain.exceptions import ProviderUnavailableError

    respx.get(f"{_CG_BASE}/simple/price").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    adapter = CoinGeckoAdapter(http_client, base_url=_CG_BASE, retry_wait=wait_none())

    with pytest.raises(ProviderUnavailableError):
        await adapter.get_quote("BTC")

    assert respx.calls.call_count == 1


@pytest.mark.asyncio
async def test_coingecko_rate_limiter_raises_triggers_retry() -> None:
    rate_limiter = AsyncMock()
    rate_limiter.check_and_increment.side_effect = [
        RateLimitError("CoinGecko"),
        RateLimitError("CoinGecko"),
        RateLimitError("CoinGecko"),
    ]
    http_client = httpx.AsyncClient()
    adapter = CoinGeckoAdapter(
        http_client,
        base_url=_CG_BASE,
        rate_limiter=rate_limiter,
        retry_wait=wait_none(),
    )

    with pytest.raises(RateLimitError):
        await adapter.get_quote("BTC")

    assert rate_limiter.check_and_increment.call_count == 3



@pytest.mark.asyncio
@respx.mock
async def test_cmc_retries_3_times_on_rate_limit(
    http_client: httpx.AsyncClient,
) -> None:
    respx.get(f"{_CMC_BASE}/cryptocurrency/quotes/latest").mock(
        return_value=httpx.Response(429, text="Too Many Requests")
    )
    adapter = CoinMarketCapAdapter(
        http_client, api_key=_API_KEY, base_url=_CMC_BASE, retry_wait=wait_none()
    )

    with pytest.raises(RateLimitError):
        await adapter.get_quote("BTC")

    assert respx.calls.call_count == 3


@pytest.mark.asyncio
@respx.mock
async def test_cmc_succeeds_after_one_retry(
    http_client: httpx.AsyncClient,
) -> None:
    ok_body = {
        "data": {
            "BTC": {
                "quote": {
                    "USD": {"price": 65000.0, "percent_change_24h": 1.5}
                }
            }
        }
    }
    respx.get(f"{_CMC_BASE}/cryptocurrency/quotes/latest").mock(
        side_effect=[
            httpx.Response(429, text="Too Many Requests"),
            httpx.Response(200, json=ok_body),
        ]
    )
    adapter = CoinMarketCapAdapter(
        http_client, api_key=_API_KEY, base_url=_CMC_BASE, retry_wait=wait_none()
    )

    quote = await adapter.get_quote("BTC")

    assert quote.symbol == "BTC"
    assert respx.calls.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_cmc_no_retry_on_server_error(
    http_client: httpx.AsyncClient,
) -> None:
    from app.services.defi.domain.exceptions import ProviderUnavailableError

    respx.get(f"{_CMC_BASE}/cryptocurrency/quotes/latest").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )
    adapter = CoinMarketCapAdapter(
        http_client, api_key=_API_KEY, base_url=_CMC_BASE, retry_wait=wait_none()
    )

    with pytest.raises(ProviderUnavailableError):
        await adapter.get_quote("BTC")

    assert respx.calls.call_count == 1


@pytest.mark.asyncio
async def test_cmc_rate_limiter_raises_triggers_retry() -> None:
    rate_limiter = AsyncMock()
    rate_limiter.check_and_increment.side_effect = [
        RateLimitError("CoinMarketCap"),
        RateLimitError("CoinMarketCap"),
        RateLimitError("CoinMarketCap"),
    ]
    http_client = httpx.AsyncClient()
    adapter = CoinMarketCapAdapter(
        http_client,
        api_key=_API_KEY,
        base_url=_CMC_BASE,
        rate_limiter=rate_limiter,
        retry_wait=wait_none(),
    )

    with pytest.raises(RateLimitError):
        await adapter.get_quote("BTC")

    assert rate_limiter.check_and_increment.call_count == 3
