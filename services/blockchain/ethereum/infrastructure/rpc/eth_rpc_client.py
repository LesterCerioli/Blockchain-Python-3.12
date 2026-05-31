from typing import Any, Optional

import httpx


class EthRpcClient:
    """
    Async JSON-RPC 2.0 client with connection pooling (SRP: only speaks JSON-RPC).
    One instance per provider; the underlying httpx.AsyncClient maintains the pool.
    """

    def __init__(self, url: str, timeout_seconds: float = 10.0) -> None:
        self._url = url
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30,
            ),
        )

    async def close(self) -> None:
        await self._http.aclose()

    async def call(self, method: str, params: Optional[list] = None) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1,
        }
        response = await self._http.post(self._url, json=payload)
        response.raise_for_status()
        body = response.json()
        if "error" in body:
            raise RuntimeError(f"JSON-RPC error from {self._url}: {body['error']}")
        return body["result"]

    async def eth_block_number(self) -> int:
        result = await self.call("eth_blockNumber")
        return int(result, 16)

    async def eth_chain_id(self) -> int:
        result = await self.call("eth_chainId")
        return int(result, 16)

    async def eth_syncing(self) -> bool:
        result = await self.call("eth_syncing")
        # eth_syncing returns False when in sync, or a dict when syncing
        return result is not False
