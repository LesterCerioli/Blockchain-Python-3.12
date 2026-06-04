import time
from decimal import Decimal
from typing import Any

import httpx
from web3 import AsyncWeb3

from ....domain.entities.swap_route import SwapHop, SwapRoute
from ....domain.interfaces.swap_service import ISwapService
from ....domain.value_objects.slippage import Slippage
from ....domain.value_objects.token_amount import TokenAmount

# Uniswap V3 QuoterV2 ABI (quoteExactInputSingle)
_QUOTER_ABI: list[dict[str, Any]] = [
    {
        "inputs": [
            {
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
                "name": "params",
                "type": "tuple",
            }
        ],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"name": "amountOut", "type": "uint256"},
            {"name": "sqrtPriceX96After", "type": "uint160"},
            {"name": "initializedTicksCrossed", "type": "uint32"},
            {"name": "gasEstimate", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

# Uniswap V3 SwapRouter02 ABI (exactInputSingle)
_ROUTER_ABI: list[dict[str, Any]] = [
    {
        "inputs": [
            {
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "recipient", "type": "address"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMinimum", "type": "uint256"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
                "name": "params",
                "type": "tuple",
            }
        ],
        "name": "exactInputSingle",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function",
    }
]

# QuoterV2 addresses per chain
_QUOTER: dict[int, str] = {
    1: "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
    137: "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
    42161: "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
    8453: "0x3d4e44Eb1374240CE5F1B136aa68B6a5C2F98a02",
}

# SwapRouter02 addresses per chain
_ROUTER: dict[int, str] = {
    1: "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
    137: "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
    42161: "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
    8453: "0x2626664c2603336E57B271c5C0b26F421741e481",
}

_DEFAULT_FEE = 3000  # 0.3% pool tier


class UniswapV3SwapAdapter(ISwapService):
    """Outbound adapter — quotes and executes swaps via Uniswap V3 on-chain contracts."""

    def __init__(
        self,
        web3_clients: dict[int, AsyncWeb3],
        token_decimals_cache: dict[tuple[str, int], int] | None = None,
    ) -> None:
        self._clients = web3_clients
        self._decimals_cache: dict[tuple[str, int], int] = token_decimals_cache or {}

    # ------------------------------------------------------------------
    # ISwapService
    # ------------------------------------------------------------------

    async def get_quote(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: TokenAmount,
        chain_id: int,
    ) -> TokenAmount:
        w3 = self._client(chain_id)
        quoter = w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(_QUOTER[chain_id]),
            abi=_QUOTER_ABI,
        )
        amount_out, *_ = await quoter.functions.quoteExactInputSingle({
            "tokenIn": AsyncWeb3.to_checksum_address(token_in_address),
            "tokenOut": AsyncWeb3.to_checksum_address(token_out_address),
            "amountIn": amount_in.raw,
            "fee": _DEFAULT_FEE,
            "sqrtPriceLimitX96": 0,
        }).call()
        decimals_out = await self._get_decimals(token_out_address, chain_id)
        return TokenAmount(
            raw=int(amount_out),
            decimals=decimals_out,
            token_address=token_out_address.lower(),
        )

    async def get_best_route(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: TokenAmount,
        chain_id: int,
    ) -> SwapRoute:
        expected_out = await self.get_quote(token_in_address, token_out_address, amount_in, chain_id)
        price_impact_bps = await self._estimate_price_impact_bps(
            token_in_address, token_out_address, amount_in, chain_id
        )
        hop = SwapHop(
            pool_address="",  # resolved off-chain via subgraph in production
            token_in_address=token_in_address.lower(),
            token_out_address=token_out_address.lower(),
            fee_bps=_DEFAULT_FEE // 10,
        )
        return SwapRoute(
            token_in_address=token_in_address.lower(),
            token_out_address=token_out_address.lower(),
            amount_in=amount_in,
            expected_amount_out=expected_out,
            price_impact_bps=price_impact_bps,
            hops=[hop],
            chain_id=chain_id,
        )

    async def get_price_impact(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: TokenAmount,
        chain_id: int,
    ) -> Decimal:
        bps = await self._estimate_price_impact_bps(
            token_in_address, token_out_address, amount_in, chain_id
        )
        return Decimal(bps) / Decimal(100)

    async def get_minimum_amount_out(
        self,
        expected_amount_out: TokenAmount,
        slippage: Slippage,
    ) -> TokenAmount:
        factor = Decimal(1) - slippage.as_percentage
        min_raw = int(Decimal(expected_amount_out.raw) * factor)
        return TokenAmount(
            raw=max(min_raw, 0),
            decimals=expected_amount_out.decimals,
            token_address=expected_amount_out.token_address,
        )

    async def execute_swap(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: TokenAmount,
        slippage: Slippage,
        recipient: str,
        chain_id: int,
    ) -> str:
        expected_out = await self.get_quote(token_in_address, token_out_address, amount_in, chain_id)
        min_out = await self.get_minimum_amount_out(expected_out, slippage)
        w3 = self._client(chain_id)
        router = w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(_ROUTER[chain_id]),
            abi=_ROUTER_ABI,
        )
        tx = await router.functions.exactInputSingle({
            "tokenIn": AsyncWeb3.to_checksum_address(token_in_address),
            "tokenOut": AsyncWeb3.to_checksum_address(token_out_address),
            "fee": _DEFAULT_FEE,
            "recipient": AsyncWeb3.to_checksum_address(recipient),
            "amountIn": amount_in.raw,
            "amountOutMinimum": min_out.raw,
            "sqrtPriceLimitX96": 0,
        }).build_transaction({"from": AsyncWeb3.to_checksum_address(recipient)})
        # Signing and broadcasting are intentionally outside this adapter;
        # the caller is responsible for wallet signing (non-custodial design).
        raise NotImplementedError(
            "execute_swap requires a signed wallet. "
            "Build the transaction via ITransactionBuilder and sign externally."
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_decimals(self, token_address: str, chain_id: int) -> int:
        key = (token_address.lower(), chain_id)
        if key not in self._decimals_cache:
            abi = [{"inputs": [], "name": "decimals", "outputs": [{"type": "uint8"}], "stateMutability": "view", "type": "function"}]
            w3 = self._client(chain_id)
            contract = w3.eth.contract(address=AsyncWeb3.to_checksum_address(token_address), abi=abi)
            self._decimals_cache[key] = await contract.functions.decimals().call()
        return self._decimals_cache[key]

    async def _estimate_price_impact_bps(
        self,
        token_in: str,
        token_out: str,
        amount_in: TokenAmount,
        chain_id: int,
    ) -> int:
        small_amount = TokenAmount(
            raw=max(amount_in.raw // 1000, 1),
            decimals=amount_in.decimals,
            token_address=amount_in.token_address,
        )
        try:
            spot_out = await self.get_quote(token_in, token_out, small_amount, chain_in := chain_id)
            full_out = await self.get_quote(token_in, token_out, amount_in, chain_id)
            if spot_out.raw == 0:
                return 0
            spot_rate = Decimal(spot_out.raw) / Decimal(small_amount.raw)
            full_rate = Decimal(full_out.raw) / Decimal(amount_in.raw)
            impact = (spot_rate - full_rate) / spot_rate
            return max(0, int(impact * 10_000))
        except Exception:
            return 0

    def _client(self, chain_id: int) -> AsyncWeb3:
        client = self._clients.get(chain_id)
        if client is None:
            raise ValueError(f"No web3 client for chain_id {chain_id}")
        return client
