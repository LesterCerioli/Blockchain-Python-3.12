from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.defi.api.dependencies import get_market_quote_service
from app.services.defi.api.routers.quotes_router import quotes_router
from app.services.defi.application.quote_service import QuoteService
from app.services.defi.domain.interfaces.market_data_provider import IMarketDataProvider
from app.services.defi.domain.interfaces.quote_cache import IQuoteCache
from app.services.defi.domain.value_objects.price import Price
from app.services.defi.domain.value_objects.price_point import PricePoint


class DictCache(IQuoteCache):
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    async def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    async def set(self, key: str, value: Any, ttl: int) -> None:
        self._store[key] = value

    async def get_many(self, keys: list[str]) -> list[Optional[Any]]:
        return [self._store.get(k) for k in keys]

    async def set_many(self, items: dict[str, Any], ttl: int) -> None:
        self._store.update(items)

    def clear(self) -> None:
        self._store.clear()


class FakeMarketDataProvider(IMarketDataProvider):
    def __init__(self, price_points: Optional[list[PricePoint]] = None) -> None:
        self.price_points = price_points or []
        self.call_count = 0

    async def get_token_price(self, token_address: str, chain_id: int) -> Optional[Price]:
        return None

    async def get_price_change_24h(self, token_address: str, chain_id: int) -> Optional[Decimal]:
        return None

    async def get_token_volume_24h(self, token_address: str, chain_id: int) -> Optional[Decimal]:
        return None

    async def get_market_cap(self, token_address: str, chain_id: int) -> Optional[Decimal]:
        return None

    async def get_historical_prices(
        self,
        token_address: str,
        chain_id: int,
        from_timestamp: int,
        to_timestamp: int,
    ) -> list[PricePoint]:
        self.call_count += 1
        return self.price_points

    async def get_market_index(self, symbol: str) -> Optional[Any]:
        return None

    async def list_market_indices(self) -> list[Any]:
        return []


BTC_TOKEN_ADDRESS = "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"
ETH_TOKEN_ADDRESS = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"


def _make_price(price_value: Decimal) -> Price:
    return Price(
        value=price_value,
        base_token_address=BTC_TOKEN_ADDRESS,
        quote_token_address="0x0000000000000000000000000000000000000000",
        chain_id=1,
    )


def _make_app(
    provider: IMarketDataProvider,
    cache: Optional[IQuoteCache] = None,
) -> FastAPI:
    app = FastAPI()
    svc = QuoteService(provider=provider, cache=cache or DictCache())
    provider_key = "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"
    app.state.defi_market_provider = provider
    app.state.defi_market_quote_service = svc
    app.dependency_overrides[get_market_quote_service] = lambda: svc
    app.include_router(quotes_router)
    return app


class TestGetOHLCVHistoryIntegration:
    def test_full_stack_returns_ohlcv_candles(self) -> None:
        ts = int(datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc).timestamp())
        provider = FakeMarketDataProvider(
            price_points=[
                PricePoint(timestamp=ts, price=_make_price(Decimal("50000"))),
                PricePoint(timestamp=ts + 60, price=_make_price(Decimal("51000"))),
                PricePoint(timestamp=ts + 120, price=_make_price(Decimal("49000"))),
            ]
        )
        app = _make_app(provider)
        client = TestClient(app)

        data = client.get(
            "/quotes/BTC/history",
            params={
                "interval": "1h",
                "from": "2026-01-15T12:00:00Z",
                "to": "2026-01-15T13:00:00Z",
            },
        ).json()

        assert data["symbol"] == "BTC"
        assert data["interval"] == "1h"
        assert isinstance(data["candles"], list)
        assert len(data["candles"]) >= 1

        candle = data["candles"][0]
        assert "open_time" in candle
        assert candle["open"] == "50000"
        assert candle["high"] == "51000"
        assert candle["low"] == "49000"
        assert candle["close"] == "49000"
        assert candle["volume"] == "0"

    def test_ohlcv_values_are_strings(self) -> None:
        ts = int(datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc).timestamp())
        provider = FakeMarketDataProvider(
            price_points=[
                PricePoint(timestamp=ts, price=_make_price(Decimal("50000"))),
            ]
        )
        app = _make_app(provider)
        client = TestClient(app)

        data = client.get(
            "/quotes/BTC/history",
            params={
                "interval": "1h",
                "from": "2026-01-15T12:00:00Z",
                "to": "2026-01-15T13:00:00Z",
            },
        ).json()

        candle = data["candles"][0]
        assert isinstance(candle["open"], str)
        assert isinstance(candle["high"], str)
        assert isinstance(candle["low"], str)
        assert isinstance(candle["close"], str)
        assert isinstance(candle["volume"], str)

    def test_invalid_interval_returns_422_before_service_call(self) -> None:
        provider = FakeMarketDataProvider()
        app = _make_app(provider)
        client = TestClient(app)

        response = client.get(
            "/quotes/BTC/history",
            params={
                "interval": "2h",
                "from": "2026-01-15T12:00:00Z",
                "to": "2026-01-15T13:00:00Z",
            },
        )

        assert response.status_code == 422
        assert provider.call_count == 0

    def test_date_range_exceeding_365_days_returns_422(self) -> None:
        provider = FakeMarketDataProvider()
        app = _make_app(provider)
        client = TestClient(app)

        response = client.get(
            "/quotes/BTC/history",
            params={
                "interval": "1h",
                "from": "2025-01-01T00:00:00Z",
                "to": "2026-06-01T00:00:00Z",
            },
        )

        assert response.status_code == 422
        assert "365" in response.json()["detail"]
        assert provider.call_count == 0

    def test_cache_hit_does_not_call_provider_on_second_request(self) -> None:
        ts = int(datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc).timestamp())
        provider = FakeMarketDataProvider(
            price_points=[
                PricePoint(timestamp=ts, price=_make_price(Decimal("50000"))),
            ]
        )
        cache = DictCache()
        app = _make_app(provider, cache=cache)
        client = TestClient(app)

        params = {
            "interval": "1h",
            "from": "2026-01-15T12:00:00Z",
            "to": "2026-01-15T13:00:00Z",
        }

        resp1 = client.get("/quotes/BTC/history", params=params)
        assert resp1.status_code == 200
        first_call_count = provider.call_count

        resp2 = client.get("/quotes/BTC/history", params=params)
        assert resp2.status_code == 200

        assert provider.call_count == first_call_count
        assert resp1.json() == resp2.json()

    def test_cache_miss_calls_provider_for_different_params(self) -> None:
        ts = int(datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc).timestamp())
        provider = FakeMarketDataProvider(
            price_points=[
                PricePoint(timestamp=ts, price=_make_price(Decimal("50000"))),
            ]
        )
        cache = DictCache()
        app = _make_app(provider, cache=cache)
        client = TestClient(app)

        client.get(
            "/quotes/BTC/history",
            params={"interval": "1h", "from": "2026-01-15T12:00:00Z", "to": "2026-01-15T13:00:00Z"},
        )

        client.get(
            "/quotes/BTC/history",
            params={"interval": "1h", "from": "2026-01-16T12:00:00Z", "to": "2026-01-16T13:00:00Z"},
        )

        assert provider.call_count == 2

    def test_candle_aggregation_multiple_intervals(self) -> None:
        base_ts = int(datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc).timestamp())
        interval_secs = 900
        bucket_0 = (base_ts // interval_secs) * interval_secs
        bucket_1 = bucket_0 + interval_secs
        provider = FakeMarketDataProvider(
            price_points=[
                PricePoint(timestamp=bucket_0, price=_make_price(Decimal("100"))),
                PricePoint(timestamp=bucket_0 + 10, price=_make_price(Decimal("110"))),
                PricePoint(timestamp=bucket_1, price=_make_price(Decimal("200"))),
                PricePoint(timestamp=bucket_1 + 600, price=_make_price(Decimal("180"))),
            ]
        )
        app = _make_app(provider)
        client = TestClient(app)

        data = client.get(
            "/quotes/BTC/history",
            params={
                "interval": "15m",
                "from": "2026-01-15T12:00:00Z",
                "to": "2026-01-15T13:00:00Z",
            },
        ).json()

        assert len(data["candles"]) == 2

        candle_0 = data["candles"][0]
        assert candle_0["open"] == "100"
        assert candle_0["high"] == "110"
        assert candle_0["low"] == "100"
        assert candle_0["close"] == "110"

        candle_1 = data["candles"][1]
        assert candle_1["open"] == "200"
        assert candle_1["high"] == "200"
        assert candle_1["low"] == "180"
        assert candle_1["close"] == "180"

    def test_interval_1m_produces_minute_candles(self) -> None:
        base_ts = int(datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc).timestamp())
        provider = FakeMarketDataProvider(
            price_points=[
                PricePoint(timestamp=base_ts, price=_make_price(Decimal("100"))),
                PricePoint(timestamp=base_ts + 30, price=_make_price(Decimal("110"))),
                PricePoint(timestamp=base_ts + 90, price=_make_price(Decimal("105"))),
            ]
        )
        app = _make_app(provider)
        client = TestClient(app)

        data = client.get(
            "/quotes/BTC/history",
            params={
                "interval": "1m",
                "from": "2026-01-15T12:00:00Z",
                "to": "2026-01-15T12:05:00Z",
            },
        ).json()

        assert len(data["candles"]) == 2
        assert data["candles"][0]["open"] == "100"
        assert data["candles"][0]["close"] == "110"
        assert data["candles"][1]["open"] == "105"
        assert data["candles"][1]["close"] == "105"

    def test_empty_price_points_returns_empty_candles(self) -> None:
        provider = FakeMarketDataProvider(price_points=[])
        app = _make_app(provider)
        client = TestClient(app)

        data = client.get(
            "/quotes/BTC/history",
            params={
                "interval": "1h",
                "from": "2026-01-15T12:00:00Z",
                "to": "2026-01-15T13:00:00Z",
            },
        ).json()

        assert data["candles"] == []

    def test_different_symbol_produces_different_symbol_in_response(self) -> None:
        ts = int(datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc).timestamp())
        provider = FakeMarketDataProvider(
            price_points=[
                PricePoint(timestamp=ts, price=_make_price(Decimal("50000"))),
            ]
        )
        app = _make_app(provider)
        client = TestClient(app)

        data = client.get(
            "/quotes/ETH/history",
            params={
                "interval": "1h",
                "from": "2026-01-15T12:00:00Z",
                "to": "2026-01-15T13:00:00Z",
            },
        ).json()

        assert data["symbol"] == "ETH"

    def test_open_time_is_iso_8601(self) -> None:
        ts = int(datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc).timestamp())
        provider = FakeMarketDataProvider(
            price_points=[
                PricePoint(timestamp=ts, price=_make_price(Decimal("50000"))),
            ]
        )
        app = _make_app(provider)
        client = TestClient(app)

        data = client.get(
            "/quotes/BTC/history",
            params={
                "interval": "1h",
                "from": "2026-01-15T12:00:00Z",
                "to": "2026-01-15T13:00:00Z",
            },
        ).json()

        dt = datetime.fromisoformat(data["candles"][0]["open_time"])
        assert dt.year == 2026

    def test_interval_1w_produces_weekly_candles(self) -> None:
        base_ts = int(datetime(2026, 1, 5, 0, 0, 0, tzinfo=timezone.utc).timestamp())
        provider = FakeMarketDataProvider(
            price_points=[
                PricePoint(timestamp=base_ts, price=_make_price(Decimal("100"))),
                PricePoint(timestamp=base_ts + 86400, price=_make_price(Decimal("110"))),
                PricePoint(timestamp=base_ts + 7 * 86400, price=_make_price(Decimal("200"))),
            ]
        )
        app = _make_app(provider)
        client = TestClient(app)

        data = client.get(
            "/quotes/BTC/history",
            params={
                "interval": "1w",
                "from": "2026-01-05T00:00:00Z",
                "to": "2026-01-26T00:00:00Z",
            },
        ).json()

        assert len(data["candles"]) == 2
