from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.defi.api.dependencies import get_market_quote_service
from app.services.defi.api.routers.quotes_router import quotes_router
from app.services.defi.application.quote_service import QuoteService
from app.services.defi.domain.entities.asset_quote import AssetQuote


def _make_client(mock_service: QuoteService) -> TestClient:
    app = FastAPI()
    app.dependency_overrides[get_market_quote_service] = lambda: mock_service
    app.include_router(quotes_router)
    return TestClient(app)


def _mock_asset_quote(
    symbol: str,
    price_usd: Decimal = Decimal("50000.00"),
    change_24h: Decimal | None = Decimal("2.5"),
    volume_24h: Decimal = Decimal("1000000000"),
    market_cap: Decimal = Decimal("900000000000"),
) -> AssetQuote:
    return AssetQuote(
        symbol=symbol,
        price_usd=price_usd,
        change_24h=change_24h,
        volume_24h=volume_24h,
        market_cap=market_cap,
        fetched_at=datetime(2026, 1, 15, 12, 30, 0, tzinfo=timezone.utc),
    )


class TestGetMarketQuoteEndpoint:

    @pytest.mark.parametrize("symbol", ["BTC", "ETH"])
    def test_returns_200_for_known_symbols(self, symbol: str):
        service = AsyncMock(spec=QuoteService)
        service.get_quote.return_value = _mock_asset_quote(symbol)
        client = _make_client(service)

        response = client.get(f"/quotes/{symbol}")

        assert response.status_code == 200

    def test_response_has_required_fields(self):
        service = AsyncMock(spec=QuoteService)
        service.get_quote.return_value = _mock_asset_quote("BTC")
        client = _make_client(service)

        data = client.get("/quotes/BTC").json()

        assert data["symbol"] == "BTC"
        assert "price_usd" in data
        assert "change_24h_pct" in data
        assert "volume_24h_usd" in data
        assert "market_cap_usd" in data
        assert "fetched_at" in data

    def test_price_usd_is_string(self):
        service = AsyncMock(spec=QuoteService)
        service.get_quote.return_value = _mock_asset_quote("BTC")
        client = _make_client(service)

        data = client.get("/quotes/BTC").json()

        assert isinstance(data["price_usd"], str)
        assert data["price_usd"] == "50000.00"

    def test_volume_24h_usd_is_string(self):
        service = AsyncMock(spec=QuoteService)
        service.get_quote.return_value = _mock_asset_quote("BTC")
        client = _make_client(service)

        data = client.get("/quotes/BTC").json()

        assert isinstance(data["volume_24h_usd"], str)

    def test_market_cap_usd_is_string(self):
        service = AsyncMock(spec=QuoteService)
        service.get_quote.return_value = _mock_asset_quote("BTC")
        client = _make_client(service)

        data = client.get("/quotes/BTC").json()

        assert isinstance(data["market_cap_usd"], str)

    def test_change_24h_pct_is_float(self):
        service = AsyncMock(spec=QuoteService)
        service.get_quote.return_value = _mock_asset_quote("BTC")
        client = _make_client(service)

        data = client.get("/quotes/BTC").json()

        assert isinstance(data["change_24h_pct"], float)

    def test_change_24h_pct_zero_when_none(self):
        service = AsyncMock(spec=QuoteService)
        service.get_quote.return_value = _mock_asset_quote("BTC", change_24h=None)
        client = _make_client(service)

        data = client.get("/quotes/BTC").json()

        assert data["change_24h_pct"] == 0.0

    def test_fetched_at_is_iso_8601(self):
        service = AsyncMock(spec=QuoteService)
        service.get_quote.return_value = _mock_asset_quote("BTC")
        client = _make_client(service)

        data = client.get("/quotes/BTC").json()

        fetched_at = datetime.fromisoformat(data["fetched_at"])
        assert fetched_at.year == 2026
        assert fetched_at.month == 1

    def test_ethereum_quote(self):
        service = AsyncMock(spec=QuoteService)
        service.get_quote.return_value = _mock_asset_quote(
            "ETH",
            price_usd=Decimal("3500.50"),
            change_24h=Decimal("-1.2"),
            volume_24h=Decimal("500000000"),
            market_cap=Decimal("420000000000"),
        )
        client = _make_client(service)

        data = client.get("/quotes/ETH").json()

        assert data["symbol"] == "ETH"
        assert data["price_usd"] == "3500.50"
        assert data["change_24h_pct"] == -1.2
        assert data["volume_24h_usd"] == "500000000"
        assert data["market_cap_usd"] == "420000000000"

    def test_returns_404_for_unknown_symbol(self):
        service = AsyncMock(spec=QuoteService)
        service.get_quote.return_value = _mock_asset_quote(
            "UNKNOWN", price_usd=Decimal(0)
        )
        client = _make_client(service)

        response = client.get("/quotes/UNKNOWN")

        assert response.status_code == 404
        assert "UNKNOWN" in response.json()["detail"]
