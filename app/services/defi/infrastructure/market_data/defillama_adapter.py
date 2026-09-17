from typing import Any, Dict, List, Optional

import httpx
from datetime import datetime, timedelta

from app.services.defi.infrastructure.cache.redis_cache import get, set


class DeFiLlamaAdapter:
    BASE_URL = "https://api.llama.fi"

    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        self._client = client or httpx.AsyncClient(base_url=self.BASE_URL, timeout=30.0)

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        cache_key = f"defillama:{endpoint}"
        cached = await get(cache_key)
        if cached is not None:
            return cached

        response = await self._client.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        await set(cache_key, data, ttl=900)
        return data

    async def get_protocols(self) -> List[Dict[str, Any]]:
        data = await self._get("/protocols")
        return data.get("data", []) or []

    async def get_historical_chain_tvl(self, chain: str) -> List[Dict[str, Any]]:
        data = await self._get(f"/v2/historicalChainTvl/{chain}")
        return data.get("data", []) or []