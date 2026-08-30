
from __future__ import annotations

import pytest
import httpx

from app.services.defi.infrastructure.market_data.coingecko_adapter import CoinGeckoAdapter
from app.services.defi.infrastructure.market_data.cmc_adapter import CoinMarketCapAdapter
from app.services.defi.infrastructure.market_data.multi_provider import MultiMarketDataProvider


@pytest.mark.integration
async def test_coingecko_get_quote_btc_live() -> None:
    async with httpx.AsyncClient() as client:
        adapter = CoinGeckoAdapter(client)
        quote = await adapter.get_quote("BTC")

    assert quote.symbol == "BTC"
    assert quote.vs_currency == "usd"
    assert quote.price > 0


@pytest.mark.integration
async def test_coingecko_get_quote_eth_live() -> None:
    async with httpx.AsyncClient() as client:
        adapter = CoinGeckoAdapter(client)
        quote = await adapter.get_quote("ETH")

    assert quote.symbol == "ETH"
    assert quote.price > 0


@pytest.mark.integration
async def test_coingecko_get_quotes_btc_eth_live() -> None:
    async with httpx.AsyncClient() as client:
        adapter = CoinGeckoAdapter(client)
        quotes = await adapter.get_quotes(["BTC", "ETH"])

    assert len(quotes) == 2
    symbols = {q.symbol for q in quotes}
    assert symbols == {"BTC", "ETH"}
    for q in quotes:
        assert q.price > 0


@pytest.mark.integration
async def test_coingecko_get_ohlcv_btc_live() -> None:
    async with httpx.AsyncClient() as client:
        adapter = CoinGeckoAdapter(client)
        candles = await adapter.get_ohlcv("BTC", days=1)

    assert len(candles) > 0
    for candle in candles:
        assert candle.high >= candle.low
        assert candle.open > 0
        assert candle.close > 0


@pytest.mark.integration
async def test_coingecko_get_quotes_sol_live() -> None:
    async with httpx.AsyncClient() as client:
        adapter = CoinGeckoAdapter(client)
        quotes = await adapter.get_quotes(["SOL"])

    assert len(quotes) == 1
    assert quotes[0].symbol == "SOL"
    assert quotes[0].price > 0


@pytest.mark.integration
async def test_cmc_get_quote_btc_live(cmc_api_key: str) -> None:
    async with httpx.AsyncClient() as client:
        adapter = CoinMarketCapAdapter(client, api_key=cmc_api_key)
        quote = await adapter.get_quote("BTC")

    assert quote.symbol == "BTC"
    assert quote.vs_currency == "usd"
    assert quote.price > 0


@pytest.mark.integration
async def test_cmc_get_quote_eth_live(cmc_api_key: str) -> None:
    async with httpx.AsyncClient() as client:
        adapter = CoinMarketCapAdapter(client, api_key=cmc_api_key)
        quote = await adapter.get_quote("ETH")

    assert quote.symbol == "ETH"
    assert quote.price > 0


@pytest.mark.integration
async def test_cmc_get_quotes_btc_eth_live(cmc_api_key: str) -> None:
    async with httpx.AsyncClient() as client:
        adapter = CoinMarketCapAdapter(client, api_key=cmc_api_key)
        quotes = await adapter.get_quotes(["BTC", "ETH"])

    assert len(quotes) == 2
    symbols = {q.symbol for q in quotes}
    assert symbols == {"BTC", "ETH"}


@pytest.mark.integration
async def test_cmc_get_ohlcv_btc_live(cmc_api_key: str) -> None:
    async with httpx.AsyncClient() as client:
        adapter = CoinMarketCapAdapter(client, api_key=cmc_api_key)
        candles = await adapter.get_ohlcv("BTC")

    assert len(candles) == 1
    candle = candles[0]
    assert candle.high >= candle.low
    assert candle.open > 0



@pytest.mark.integration
async def test_multi_provider_coingecko_fallback_live(cmc_api_key: str) -> None:
    async with httpx.AsyncClient() as client:
        cg = CoinGeckoAdapter(client)
        cmc = CoinMarketCapAdapter(client, api_key=cmc_api_key)
        mp = MultiMarketDataProvider([cg, cmc])
        quote = await mp.get_quote("BTC")

    assert quote.symbol == "BTC"
    assert quote.price > 0
