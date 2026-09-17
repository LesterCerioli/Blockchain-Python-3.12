from decimal import Decimal
from typing import Any

from web3 import AsyncWeb3

from ....domain.entities.unsigned_transaction import UnsignedTransaction
from ....domain.interfaces.transaction_builder import ITransactionBuilder
from ....domain.value_objects.token_amount import TokenAmount


_ERC20_APPROVE_ABI: list[dict[str, Any]] = [
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

_WETH_ABI: list[dict[str, Any]] = [
    {
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "inputs": [{"name": "wad", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]

_WETH: dict[int, str] = {
    1: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    137: "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",  # WMATIC
    42161: "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
    8453: "0x4200000000000000000000000000000000000006",
}


class Web3TransactionBuilderAdapter(ITransactionBuilder):
    
    def __init__(
        self,
        web3_clients: dict[int, AsyncWeb3],
        router_addresses: dict[int, str],
    ) -> None:
        self._clients = web3_clients
        self._routers = router_addresses

    
    async def build_approve(
        self,
        from_address: str,
        token_address: str,
        spender_address: str,
        amount: TokenAmount,
        chain_id: int,
    ) -> UnsignedTransaction:
        w3 = self._client(chain_id)
        contract = w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(token_address),
            abi=_ERC20_APPROVE_ABI,
        )
        data: str = contract.encodeABI("approve", [
            AsyncWeb3.to_checksum_address(spender_address),
            amount.raw,
        ])
        nonce = await w3.eth.get_transaction_count(
            AsyncWeb3.to_checksum_address(from_address), "pending"
        )
        gas_price = await w3.eth.gas_price
        return UnsignedTransaction(
            to=token_address.lower(),
            from_address=from_address.lower(),
            value=Decimal(0),
            data=data,
            gas=60_000,
            gas_price=Decimal(gas_price),
            nonce=nonce,
            chain_id=chain_id,
        )

    async def build_swap(
        self,
        from_address: str,
        token_in_address: str,
        token_out_address: str,
        amount_in: TokenAmount,
        min_amount_out: TokenAmount,
        deadline: int,
        chain_id: int,
    ) -> UnsignedTransaction:
        
        raise NotImplementedError(
            "build_swap requires a router-specific ABI. "
            "Use UniswapV3SwapAdapter.execute_swap for end-to-end swaps."
        )

    async def build_add_liquidity(
        self,
        from_address: str,
        pool_address: str,
        amount0: TokenAmount,
        amount1: TokenAmount,
        min_amount0: TokenAmount,
        min_amount1: TokenAmount,
        deadline: int,
        chain_id: int,
    ) -> UnsignedTransaction:
        raise NotImplementedError(
            "build_add_liquidity requires the pool-specific ABI (V2/V3 differ significantly)."
        )

    async def build_remove_liquidity(
        self,
        from_address: str,
        pool_address: str,
        liquidity: int,
        min_amount0: TokenAmount,
        min_amount1: TokenAmount,
        deadline: int,
        chain_id: int,
    ) -> UnsignedTransaction:
        raise NotImplementedError(
            "build_remove_liquidity requires the pool-specific ABI."
        )

    async def build_wrap_eth(
        self,
        from_address: str,
        amount_wei: int,
        chain_id: int,
    ) -> UnsignedTransaction:
        weth_address = self._weth(chain_id)
        w3 = self._client(chain_id)
        contract = w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(weth_address),
            abi=_WETH_ABI,
        )
        data: str = contract.encodeABI("deposit", [])
        nonce = await w3.eth.get_transaction_count(
            AsyncWeb3.to_checksum_address(from_address), "pending"
        )
        gas_price = await w3.eth.gas_price
        return UnsignedTransaction(
            to=weth_address.lower(),
            from_address=from_address.lower(),
            value=Decimal(amount_wei),
            data=data,
            gas=46_000,
            gas_price=Decimal(gas_price),
            nonce=nonce,
            chain_id=chain_id,
        )

    async def build_unwrap_weth(
        self,
        from_address: str,
        amount_wei: int,
        chain_id: int,
    ) -> UnsignedTransaction:
        weth_address = self._weth(chain_id)
        w3 = self._client(chain_id)
        contract = w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(weth_address),
            abi=_WETH_ABI,
        )
        data: str = contract.encodeABI("withdraw", [amount_wei])
        nonce = await w3.eth.get_transaction_count(
            AsyncWeb3.to_checksum_address(from_address), "pending"
        )
        gas_price = await w3.eth.gas_price
        return UnsignedTransaction(
            to=weth_address.lower(),
            from_address=from_address.lower(),
            value=Decimal(0),
            data=data,
            gas=46_000,
            gas_price=Decimal(gas_price),
            nonce=nonce,
            chain_id=chain_id,
        )

    
    def _client(self, chain_id: int) -> AsyncWeb3:
        client = self._clients.get(chain_id)
        if client is None:
            raise ValueError(f"No web3 client for chain_id {chain_id}")
        return client

    @staticmethod
    def _weth(chain_id: int) -> str:
        address = _WETH.get(chain_id)
        if address is None:
            raise ValueError(f"No WETH address configured for chain_id {chain_id}")
        return address
