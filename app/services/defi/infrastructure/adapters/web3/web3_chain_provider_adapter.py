from typing import Any, Optional

from web3 import AsyncWeb3

from ....domain.entities.chain_info import ChainInfo
from ....domain.interfaces.chain_provider import IChainProvider

_CHAIN_META: dict[int, dict[str, Any]] = {
    1: {
        "name": "Ethereum Mainnet",
        "native_token_symbol": "ETH",
        "block_time_seconds": 12,
        "explorer_url": "https://etherscan.io",
    },
    137: {
        "name": "Polygon",
        "native_token_symbol": "MATIC",
        "block_time_seconds": 2,
        "explorer_url": "https://polygonscan.com",
    },
    42161: {
        "name": "Arbitrum One",
        "native_token_symbol": "ETH",
        "block_time_seconds": 1,
        "explorer_url": "https://arbiscan.io",
    },
    8453: {
        "name": "Base",
        "native_token_symbol": "ETH",
        "block_time_seconds": 2,
        "explorer_url": "https://basescan.org",
    },
}


class Web3ChainProviderAdapter(IChainProvider):
    
    def __init__(self, web3_clients: dict[int, AsyncWeb3]) -> None:
        self._clients = web3_clients

    
    async def get_block_number(self, chain_id: int) -> int:
        return await self._client(chain_id).eth.block_number

    async def get_block_timestamp(self, chain_id: int, block_number: int) -> int:
        block = await self._client(chain_id).eth.get_block(block_number)
        return int(block["timestamp"])

    async def get_chain_info(self, chain_id: int) -> ChainInfo:
        meta = _CHAIN_META.get(chain_id)
        if meta is None:
            raise ValueError(f"No chain metadata registered for chain_id {chain_id}")
        return ChainInfo(chain_id=chain_id, **meta)

    async def is_contract(self, chain_id: int, address: str) -> bool:
        code = await self._client(chain_id).eth.get_code(
            AsyncWeb3.to_checksum_address(address)
        )
        return code not in (b"", b"0x")

    async def get_transaction_receipt(
        self,
        chain_id: int,
        tx_hash: str,
    ) -> Optional[dict[str, Any]]:
        try:
            receipt = await self._client(chain_id).eth.get_transaction_receipt(tx_hash)
            return dict(receipt) if receipt else None
        except Exception:
            return None

    async def call_view(
        self,
        chain_id: int,
        contract_address: str,
        encoded_call: str,
    ) -> str:
        result = await self._client(chain_id).eth.call(
            {
                "to": AsyncWeb3.to_checksum_address(contract_address),
                "data": encoded_call,
            }
        )
        return result.hex()

    
    def _client(self, chain_id: int) -> AsyncWeb3:
        client = self._clients.get(chain_id)
        if client is None:
            raise ValueError(f"No web3 client configured for chain_id {chain_id}")
        return client
