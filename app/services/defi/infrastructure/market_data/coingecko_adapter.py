from datetime import datetime, timezone
from decimal import Decimal

import httpx

from ...domain.exceptions import ProviderUnavailableError, RateLimitError
from ...domain.interfaces.market_data_provider import IMarketDataProvider
from ...domain.value_objects.market_quote import MarketQuote
from ...domain.value_objects.ohlcv_candle import OHLCVCandle

_PROVIDER_NAME = "CoinGecko"
_BASE_URL = "https://api.coingecko.com/api/v3"

# Maps well-known ticker symbols to CoinGecko coin IDs.
SYMBOL_TO_COIN_ID: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
}


def _resolve_coin_id(symbol: str) -> str:
    upper = symbol.upper()
    return SYMBOL_TO_COIN_ID.get(upper, upper.lower())


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code == 429:
        raise RateLimitError(_PROVIDER_NAME)
    if response.status_code >= 500:
        raise ProviderUnavailableError(_PROVIDER_NAME, response.status_code)
    response.raise_for_status()


class CoinGeckoAdapter(IMarketDataProvider):

    def __init__(self, client: httpx.AsyncClient, base_url: str = _BASE_URL) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")

    async def get_quote(self, symbol: str, vs_currency: str = "usd") -> MarketQuote:
        coin_id = _resolve_coin_id(symbol)
        response = await self._client.get(
            f"{self._base_url}/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": vs_currency,
                "include_24hr_change": "true",
            },
        )
        _raise_for_status(response)
        data = response.json()
        coin_data = data[coin_id]
        return MarketQuote(
            symbol=symbol.upper(),
            vs_currency=vs_currency.lower(),
            price=Decimal(str(coin_data[vs_currency.lower()])),
            price_change_24h=(
                Decimal(str(coin_data[f"{vs_currency.lower()}_24h_change"]))
                if f"{vs_currency.lower()}_24h_change" in coin_data
                else None
            ),
            timestamp=datetime.now(tz=timezone.utc),
        )

    async def get_quotes(
        self, symbols: list[str], vs_currency: str = "usd"
    ) -> list[MarketQuote]:
        coin_ids = [_resolve_coin_id(s) for s in symbols]
        symbol_map = {_resolve_coin_id(s): s.upper() for s in symbols}

        response = await self._client.get(
            f"{self._base_url}/simple/price",
            params={
                "ids": ",".join(coin_ids),
                "vs_currencies": vs_currency,
                "include_24hr_change": "true",
            },
        )
        _raise_for_status(response)
        data = response.json()
        now = datetime.now(tz=timezone.utc)
        quotes: list[MarketQuote] = []
        for coin_id in coin_ids:
            if coin_id not in data:
                continue
            coin_data = data[coin_id]
            vs = vs_currency.lower()
            quotes.append(
                MarketQuote(
                    symbol=symbol_map[coin_id],
                    vs_currency=vs,
                    price=Decimal(str(coin_data[vs])),
                    price_change_24h=(
                        Decimal(str(coin_data[f"{vs}_24h_change"]))
                        if f"{vs}_24h_change" in coin_data
                        else None
                    ),
                    timestamp=now,
                )
            )
        return quotes

    async def get_ohlcv(
        self, symbol: str, vs_currency: str = "usd", days: int = 1
    ) -> list[OHLCVCandle]:
        coin_id = _resolve_coin_id(symbol)
        response = await self._client.get(
            f"{self._base_url}/coins/{coin_id}/ohlc",
            params={"vs_currency": vs_currency, "days": days},
        )
        _raise_for_status(response)
        # Each entry: [timestamp_ms, open, high, low, close]
        raw: list[list[float]] = response.json()
        return [
            OHLCVCandle(
                timestamp=datetime.fromtimestamp(entry[0] / 1000, tz=timezone.utc),
                open=Decimal(str(entry[1])),
                high=Decimal(str(entry[2])),
                low=Decimal(str(entry[3])),
                close=Decimal(str(entry[4])),
            )
            for entry in raw
        ]
