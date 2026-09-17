from decimal import Decimal
from typing import Optional

import httpx

from ....domain.entities.market_index import MarketIndex
from ....domain.interfaces.market_data_provider import IMarketDataProvider
from ....domain.value_objects.price import Price
from ....domain.value_objects.price_point import PricePoint

_USD_PLACEHOLDER = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"

_CHAIN_PLATFORM: dict[int, str] = {
    1: "ethereum",
    137: "polygon-pos",
    42161: "arbitrum-one",
    8453: "base",
}


class CoinGeckoMarketDataAdapter(IMarketDataProvider):
    """Outbound adapter — maps CoinGecko REST API to IMarketDataProvider."""

    _BASE = "https://api.coingecko.com/api/v3"

    def __init__(self, http_client: httpx.AsyncClient, api_key: str = "") -> None:
        self._client = http_client
        self._headers = {"x-cg-pro-api-key": api_key} if api_key else {}

    
    async def get_token_price(self, token_address: str, chain_id: int) -> Optional[Price]:
        data = await self._simple_token_price(token_address, chain_id, extras=[])
        raw = data.get("usd")
        if raw is None:
            return None
        return self._to_price(token_address, chain_id, raw)

    async def get_price_change_24h(self, token_address: str, chain_id: int) -> Optional[Decimal]:
        data = await self._simple_token_price(
            token_address, chain_id, extras=["include_24hr_change=true"]
        )
        raw = data.get("usd_24h_change")
        return Decimal(str(raw)) if raw is not None else None

    async def get_token_volume_24h(self, token_address: str, chain_id: int) -> Optional[Decimal]:
        data = await self._simple_token_price(
            token_address, chain_id, extras=["include_24hr_vol=true"]
        )
        raw = data.get("usd_24h_vol")
        return Decimal(str(raw)) if raw is not None else None

    async def get_market_cap(self, token_address: str, chain_id: int) -> Optional[Decimal]:
        data = await self._simple_token_price(
            token_address, chain_id, extras=["include_market_cap=true"]
        )
        raw = data.get("usd_market_cap")
        return Decimal(str(raw)) if raw is not None else None

    async def get_historical_prices(
        self,
        token_address: str,
        chain_id: int,
        from_timestamp: int,
        to_timestamp: int,
    ) -> list[PricePoint]:
        platform = self._platform(chain_id)
        resp = await self._client.get(
            f"{self._BASE}/coins/{platform}/contract/{token_address}/market_chart/range",
            headers=self._headers,
            params={"vs_currency": "usd", "from": from_timestamp, "to": to_timestamp},
        )
        resp.raise_for_status()
        return [
            PricePoint(
                timestamp=int(ts_ms / 1000),
                price=self._to_price(token_address, chain_id, value),
            )
            for ts_ms, value in resp.json().get("prices", [])
        ]

    async def get_market_index(self, symbol: str) -> Optional[MarketIndex]:
        resp = await self._client.get(
            f"{self._BASE}/global",
            headers=self._headers,
        )
        resp.raise_for_status()
        
        raise NotImplementedError(
            "CoinGecko does not expose named indices by symbol; use a dedicated index provider."
        )

    async def list_market_indices(self) -> list[MarketIndex]:
        raise NotImplementedError(
            "CoinGecko does not expose a named-index list; use a dedicated index provider."
        )

    
    async def _simple_token_price(
        self,
        token_address: str,
        chain_id: int,
        extras: list[str],
    ) -> dict:
        platform = self._platform(chain_id)
        params: dict = {
            "contract_addresses": token_address.lower(),
            "vs_currencies": "usd",
        }
        for kv in extras:
            k, v = kv.split("=", 1)
            params[k] = v
        resp = await self._client.get(
            f"{self._BASE}/simple/token_price/{platform}",
            headers=self._headers,
            params=params,
        )
        resp.raise_for_status()
        return resp.json().get(token_address.lower(), {})

    @staticmethod
    def _platform(chain_id: int) -> str:
        platform = _CHAIN_PLATFORM.get(chain_id)
        if platform is None:
            raise ValueError(f"Unsupported chain_id for CoinGecko adapter: {chain_id}")
        return platform

    @staticmethod
    def _to_price(token_address: str, chain_id: int, raw: float | Decimal) -> Price:
        return Price(
            value=Decimal(str(raw)),
            base_token_address=token_address.lower(),
            quote_token_address=_USD_PLACEHOLDER,
            chain_id=chain_id,
        )
