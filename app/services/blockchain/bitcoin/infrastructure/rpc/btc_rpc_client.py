from typing import Any, Optional

import httpx


class BtcRpcClient:
    
    def __init__(
        self,
        url: str,
        rpc_user: str,
        rpc_password: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._url = url
        self._http = httpx.AsyncClient(
            auth=(rpc_user, rpc_password),
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
            "jsonrpc": "1.0",
            "method": method,
            "params": params or [],
            "id": 1,
        }
        response = await self._http.post(self._url, json=payload)
        response.raise_for_status()
        body = response.json()
        if body.get("error") is not None:
            raise RuntimeError(f"Bitcoin RPC error from {self._url}: {body['error']}")
        return body["result"]

    async def get_block_count(self) -> int:
        return int(await self.call("getblockcount"))

    async def get_blockchain_info(self) -> dict:
        return await self.call("getblockchaininfo")

    async def get_network(self) -> str:
        info = await self.get_blockchain_info()
        return info["chain"]

    async def is_syncing(self) -> bool:
        info = await self.get_blockchain_info()
        return bool(info.get("initialblockdownload", False))
