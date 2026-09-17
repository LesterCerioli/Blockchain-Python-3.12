from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from unittest.mock import AsyncMock

import pytest

from app.services.defi.application.quote_service import QuoteService
from app.services.defi.domain.entities.asset_quote import AssetQuote
from app.services.defi.domain.value_objects.ohlcv_candle import OHLCVCandle


@pytest.fixture
def mock_provider() -> AsyncMock:
    provider = AsyncMock()
    provider.get_token_price = AsyncMock(return_value=AsyncMock(value=Decimal("65000")))
    provider.get_price_change_24h = AsyncMock(return_value=Decimal("1.5"))
    provider.get_token_volume_24h = AsyncMock(return_value=Decimal("1e9"))
    provider.get_market_cap = AsyncMock(return_value=Decimal("1.3e12"))
    provider.get_historical_prices = AsyncMock(return_value=[])
    return provider


@pytest.fixture
def mock_cache() -> AsyncMock:
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.get_many = AsyncMock(return_value=[None])
    cache.set = AsyncMock()
    cache.set_many = AsyncMock()
    return cache


def _quote(symbol: str = "BTC") -> AssetQuote:
    return AssetQuote(
        symbol=symbol,
        price_usd=Decimal("65000"),
        change_24h=Decimal("1.5"),
        volume_24h=Decimal("1e9"),
        market_cap=Decimal("1.3e12"),
    )


# ---------------------------------------------------------------------------
# get_quote – cache hit
# ---------------------------------------------------------------------------


class TestGetQuoteCacheHit:
    @pytest.mark.asyncio
    async def test_returns_cached_quote_without_calling_provider(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        expected = _quote("BTC")
        mock_cache.get.return_value = expected

        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_quote("BTC")

        assert result == expected
        mock_cache.get.assert_awaited_once_with("quote:BTC")
        mock_provider.get_token_price.assert_not_awaited()
        mock_provider.get_price_change_24h.assert_not_awaited()
        mock_provider.get_token_volume_24h.assert_not_awaited()
        mock_provider.get_market_cap.assert_not_awaited()
        mock_cache.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_symbol_is_normalized_to_uppercase(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        expected = _quote("BTC")
        mock_cache.get.return_value = expected

        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_quote("btc")

        assert result.symbol == "BTC"
        mock_cache.get.assert_awaited_once_with("quote:BTC")


# ---------------------------------------------------------------------------
# get_quote – cache miss
# ---------------------------------------------------------------------------


class TestGetQuoteCacheMiss:
    @pytest.mark.asyncio
    async def test_calls_provider_and_populates_cache(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        mock_cache.get.return_value = None

        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_quote("BTC")

        assert result.symbol == "BTC"
        assert result.price_usd == Decimal("65000")
        mock_provider.get_token_price.assert_awaited_once()
        mock_provider.get_price_change_24h.assert_awaited_once()
        mock_provider.get_token_volume_24h.assert_awaited_once()
        mock_provider.get_market_cap.assert_awaited_once()
        mock_cache.set.assert_awaited_once()
        key = mock_cache.set.call_args[0][0]
        assert key == "quote:BTC"

    @pytest.mark.asyncio
    async def test_cached_quote_has_correct_fields(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        mock_cache.get.return_value = None

        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_quote("ETH")

        assert isinstance(result, AssetQuote)
        assert result.symbol == "ETH"
        assert isinstance(result.price_usd, Decimal)
        assert isinstance(result.change_24h, Decimal)
        assert isinstance(result.volume_24h, Decimal)
        assert isinstance(result.market_cap, Decimal)
        assert isinstance(result.fetched_at, datetime)
        assert result.fetched_at.tzinfo is not None


# ---------------------------------------------------------------------------
# get_market_quotes – symbol normalization
# ---------------------------------------------------------------------------


class TestGetMarketQuotes:
    @pytest.mark.asyncio
    async def test_parses_comma_separated_string(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        btc = _quote("BTC")
        eth = _quote("ETH")
        mock_cache.get_many.return_value = [btc, eth]

        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_market_quotes("BTC,ETH")

        assert len(result) == 2
        assert result[0].symbol == "BTC"
        assert result[1].symbol == "ETH"

    @pytest.mark.asyncio
    async def test_trims_whitespace_around_symbols(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        btc = _quote("BTC")
        sol = _quote("SOL")
        mock_cache.get_many.return_value = [btc, sol]

        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_market_quotes("  BTC , SOL  ")

        assert len(result) == 2
        assert result[0].symbol == "BTC"
        assert result[1].symbol == "SOL"

    @pytest.mark.asyncio
    async def test_uppercases_lowercase_input(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        btc = _quote("BTC")
        mock_cache.get_many.return_value = [btc]

        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_market_quotes("btc")

        assert len(result) == 1
        assert result[0].symbol == "BTC"

    @pytest.mark.asyncio
    async def test_skips_empty_segments(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        btc = _quote("BTC")
        eth = _quote("ETH")
        mock_cache.get_many.return_value = [btc, eth]

        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_market_quotes("BTC,,,ETH")

        assert len(result) == 2
        assert result[0].symbol == "BTC"
        assert result[1].symbol == "ETH"

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_blank_string(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_market_quotes("")

        assert result == []

    @pytest.mark.asyncio
    async def test_delegates_to_get_quotes(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        mock_cache.get_many.return_value = [None, None]

        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_market_quotes("BTC,ETH")

        assert len(result) == 2
        assert {q.symbol for q in result} == {"BTC", "ETH"}


# ---------------------------------------------------------------------------
# get_quotes – empty list
# ---------------------------------------------------------------------------


class TestGetQuotesEmpty:
    @pytest.mark.asyncio
    async def test_returns_empty_list_without_calling_provider_or_cache(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_quotes([])

        assert result == []
        mock_cache.get_many.assert_not_awaited()
        mock_cache.get.assert_not_awaited()
        mock_provider.get_token_price.assert_not_awaited()
        mock_cache.set.assert_not_awaited()
        mock_cache.set_many.assert_not_awaited()


# ---------------------------------------------------------------------------
# get_quotes – all cached
# ---------------------------------------------------------------------------


class TestGetQuotesAllCached:
    @pytest.mark.asyncio
    async def test_returns_all_from_cache_without_calling_provider(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        btc = _quote("BTC")
        eth = _quote("ETH")
        mock_cache.get_many.return_value = [btc, eth]

        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_quotes(["BTC", "ETH"])

        assert len(result) == 2
        assert result[0].symbol == "BTC"
        assert result[1].symbol == "ETH"
        mock_cache.get_many.assert_awaited_once()
        mock_provider.get_token_price.assert_not_awaited()
        mock_cache.set.assert_not_awaited()


# ---------------------------------------------------------------------------
# get_quotes – all cache miss
# ---------------------------------------------------------------------------


class TestGetQuotesAllMiss:
    @pytest.mark.asyncio
    async def test_fetches_all_from_provider_and_caches_each(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        mock_cache.get_many.return_value = [None, None]

        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_quotes(["BTC", "ETH"])

        assert len(result) == 2
        assert {q.symbol for q in result} == {"BTC", "ETH"}
        assert mock_provider.get_token_price.await_count >= 2
        assert mock_cache.set.await_count == 2


# ---------------------------------------------------------------------------
# get_quotes – mixed cache
# ---------------------------------------------------------------------------


class TestGetQuotesMixed:
    @pytest.mark.asyncio
    async def test_only_uncached_symbols_call_provider(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        btc = _quote("BTC")
        mock_cache.get_many.return_value = [btc, None]

        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_quotes(["BTC", "ETH"])

        assert len(result) == 2
        assert mock_cache.get_many.await_count == 1
        assert mock_provider.get_token_price.await_count >= 1
        assert mock_cache.set.await_count == 1


# ---------------------------------------------------------------------------
# _fetch_and_cache (error handling)
# ---------------------------------------------------------------------------


class TestFetchAndCacheErrorHandling:
    @pytest.mark.asyncio
    async def test_handles_none_from_provider_gracefully(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        mock_cache.get.return_value = None
        mock_provider.get_token_price.return_value = None
        mock_provider.get_price_change_24h.return_value = None
        mock_provider.get_token_volume_24h.return_value = None
        mock_provider.get_market_cap.return_value = None

        svc = QuoteService(mock_provider, mock_cache)
        result = await svc.get_quote("BTC")

        assert result.price_usd == Decimal("0")
        assert result.change_24h is None
        assert result.volume_24h == Decimal("0")
        assert result.market_cap == Decimal("0")


# ---------------------------------------------------------------------------
# get_ohlcv
# ---------------------------------------------------------------------------


class TestGetOhlcv:
    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_candles_without_calling_provider(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        candles = [
            OHLCVCandle(
                timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
                open=Decimal("100"),
                high=Decimal("110"),
                low=Decimal("90"),
                close=Decimal("105"),
            )
        ]
        mock_cache.get.return_value = candles

        svc = QuoteService(mock_provider, mock_cache)
        from_ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_ts = datetime(2024, 1, 2, tzinfo=timezone.utc)
        result = await svc.get_ohlcv("BTC", "1h", from_ts, to_ts)

        assert result == candles
        mock_cache.get.assert_awaited_once()
        mock_provider.get_historical_prices.assert_not_awaited()
        mock_cache.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cache_miss_calls_provider_and_caches(
        self,
        mock_provider: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        mock_cache.get.return_value = None
        mock_provider.get_historical_prices.return_value = []

        svc = QuoteService(mock_provider, mock_cache)
        from_ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_ts = datetime(2024, 1, 2, tzinfo=timezone.utc)
        result = await svc.get_ohlcv("BTC", "1h", from_ts, to_ts)

        assert result == []
        mock_provider.get_historical_prices.assert_awaited_once()
        mock_cache.set.assert_awaited_once()
