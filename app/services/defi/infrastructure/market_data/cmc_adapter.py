from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ...domain.exceptions import ProviderUnavailableError, RateLimitError
from ...domain.value_objects.market_quote import MarketQuote
from ...domain.value_objects.ohlcv_candle import OHLCVCandle

if TYPE_CHECKING:
    from tenacity.wait import wait_base
    from .rate_limiter import RedisRateLimiter

_PROVIDER_NAME = "CoinMarketCap"
_BASE_URL = "https://pro-api.coinmarketcap.com/v1"
_DEFAULT_RETRY_ATTEMPTS = 3
_DEFAULT_RETRY_WAIT = wait_exponential(multiplier=1, min=2, max=30)


class CoinMarketCapAdapter:

    def __init__(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        base_url: str = _BASE_URL,
        rate_limiter: RedisRateLimiter | None = None,
        retry_wait: wait_base | None = None,
        retry_attempts: int = _DEFAULT_RETRY_ATTEMPTS,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._headers = {"X-CMC_PRO_API_KEY": api_key, "Accept": "application/json"}
        self._rate_limiter = rate_limiter
        self._retry_wait = retry_wait if retry_wait is not None else _DEFAULT_RETRY_WAIT
        self._retry_attempts = retry_attempts

    def _retrying(self) -> AsyncRetrying:
        return AsyncRetrying(
            retry=retry_if_exception_type(RateLimitError),
            wait=self._retry_wait,
            stop=stop_after_attempt(self._retry_attempts),
            reraise=True,
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 0)) or None
            raise RateLimitError(_PROVIDER_NAME, retry_after)
        if response.status_code >= 500:
            raise ProviderUnavailableError(_PROVIDER_NAME, response.status_code)
        response.raise_for_status()

    async def get_quote(self, symbol: str, vs_currency: str = "usd") -> MarketQuote:
        async for attempt in self._retrying():
            with attempt:
                if self._rate_limiter:
                    await self._rate_limiter.check_and_increment()
                response = await self._client.get(
                    f"{self._base_url}/cryptocurrency/quotes/latest",
                    headers=self._headers,
                    params={"symbol": symbol.upper(), "convert": vs_currency.upper()},
                )
                self._raise_for_status(response)
                data = response.json()["data"][symbol.upper()]
                quote_data = data["quote"][vs_currency.upper()]
                return MarketQuote(
                    symbol=symbol.upper(),
                    vs_currency=vs_currency.lower(),
                    price=Decimal(str(quote_data["price"])),
                    price_change_24h=(
                        Decimal(str(quote_data["percent_change_24h"]))
                        if quote_data.get("percent_change_24h") is not None
                        else None
                    ),
                    timestamp=datetime.now(tz=timezone.utc),
                )

    async def get_quotes(
        self, symbols: list[str], vs_currency: str = "usd"
    ) -> list[MarketQuote]:
        async for attempt in self._retrying():
            with attempt:
                if self._rate_limiter:
                    await self._rate_limiter.check_and_increment()
                upper_symbols = [s.upper() for s in symbols]
                response = await self._client.get(
                    f"{self._base_url}/cryptocurrency/quotes/latest",
                    headers=self._headers,
                    params={
                        "symbol": ",".join(upper_symbols),
                        "convert": vs_currency.upper(),
                    },
                )
                self._raise_for_status(response)
                now = datetime.now(tz=timezone.utc)
                vs = vs_currency.upper()
                quotes: list[MarketQuote] = []
                for sym, coin_data in response.json()["data"].items():
                    quote_data = coin_data["quote"][vs]
                    quotes.append(
                        MarketQuote(
                            symbol=sym,
                            vs_currency=vs_currency.lower(),
                            price=Decimal(str(quote_data["price"])),
                            price_change_24h=(
                                Decimal(str(quote_data["percent_change_24h"]))
                                if quote_data.get("percent_change_24h") is not None
                                else None
                            ),
                            timestamp=now,
                        )
                    )
                return quotes

    async def get_ohlcv(
        self, symbol: str, vs_currency: str = "usd", days: int = 1
    ) -> list[OHLCVCandle]:
        async for attempt in self._retrying():
            with attempt:
                if self._rate_limiter:
                    await self._rate_limiter.check_and_increment()
                response = await self._client.get(
                    f"{self._base_url}/cryptocurrency/ohlcv/latest",
                    headers=self._headers,
                    params={
                        "symbol": symbol.upper(),
                        "convert": vs_currency.upper(),
                    },
                )
                self._raise_for_status(response)
                data = response.json()["data"][symbol.upper()]
                candle = data["quote"][vs_currency.upper()]
                return [
                    OHLCVCandle(
                        timestamp=datetime.now(tz=timezone.utc),
                        open=Decimal(str(candle["open"])),
                        high=Decimal(str(candle["high"])),
                        low=Decimal(str(candle["low"])),
                        close=Decimal(str(candle["close"])),
                    )
                ]
