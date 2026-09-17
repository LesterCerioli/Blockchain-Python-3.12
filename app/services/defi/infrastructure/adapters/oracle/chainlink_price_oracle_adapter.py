from decimal import Decimal
from typing import Any, Optional

from web3 import AsyncWeb3

from ....domain.interfaces.price_oracle import IPriceOracle
from ....domain.value_objects.price import Price


_AGGREGATOR_ABI: list[dict[str, Any]] = [
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"name": "roundId", "type": "uint80"},
            {"name": "answer", "type": "int256"},
            {"name": "startedAt", "type": "uint256"},
            {"name": "updatedAt", "type": "uint256"},
            {"name": "answeredInRound", "type": "uint80"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class ChainlinkPriceOracleAdapter(IPriceOracle):
    
    def __init__(
        self,
        web3_clients: dict[int, AsyncWeb3],
        feed_registry: dict[tuple[str, str, int], str],
        staleness_threshold_seconds: int = 3600,
    ) -> None:
        
        self._clients = web3_clients
        self._feeds = feed_registry
        self._staleness_seconds = staleness_threshold_seconds

    
    async def get_price(
        self,
        base_token_address: str,
        quote_token_address: str,
        chain_id: int,
    ) -> Optional[Price]:
        result = await self._latest_round(base_token_address, quote_token_address, chain_id)
        if result is None:
            return None
        answer, _, decimals = result
        return Price(
            value=Decimal(answer) / Decimal(10**decimals),
            base_token_address=base_token_address.lower(),
            quote_token_address=quote_token_address.lower(),
            chain_id=chain_id,
        )

    async def get_price_usd(self, token_address: str, chain_id: int) -> Optional[Price]:
        usd_feed = "0x0000000000000000000000000000000000000348"  # Chainlink USD sentinel
        return await self.get_price(token_address, usd_feed, chain_id)

    async def get_twap(
        self,
        base_token_address: str,
        quote_token_address: str,
        period_seconds: int,
        chain_id: int,
    ) -> Optional[Price]:
        
        raise NotImplementedError(
            "TWAP is not available via Chainlink AggregatorV3. "
            "Use a Uniswap V3 TWAP oracle for time-weighted averages."
        )

    async def get_price_with_confidence(
        self,
        base_token_address: str,
        quote_token_address: str,
        chain_id: int,
    ) -> tuple[Optional[Price], Decimal]:
        result = await self._latest_round(base_token_address, quote_token_address, chain_id)
        if result is None:
            return None, Decimal(0)
        answer, updated_at, decimals = result
        import time
        age = int(time.time()) - updated_at
        confidence = Decimal(1) if age < self._staleness_seconds else Decimal("0.5")
        price = Price(
            value=Decimal(answer) / Decimal(10**decimals),
            base_token_address=base_token_address.lower(),
            quote_token_address=quote_token_address.lower(),
            chain_id=chain_id,
        )
        return price, confidence

    async def is_price_stale(
        self,
        base_token_address: str,
        quote_token_address: str,
        chain_id: int,
        max_age_seconds: int,
    ) -> bool:
        import time
        result = await self._latest_round(base_token_address, quote_token_address, chain_id)
        if result is None:
            return True
        _, updated_at, _ = result
        return (int(time.time()) - updated_at) > max_age_seconds

    
    async def _latest_round(
        self,
        base: str,
        quote: str,
        chain_id: int,
    ) -> Optional[tuple[int, int, int]]:
        
        feed_address = self._feeds.get((base.lower(), quote.lower(), chain_id))
        if feed_address is None:
            return None
        w3 = self._clients[chain_id]
        aggregator = w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(feed_address),
            abi=_AGGREGATOR_ABI,
        )
        _, answer, _, updated_at, _ = await aggregator.functions.latestRoundData().call()
        decimals: int = await aggregator.functions.decimals().call()
        return int(answer), int(updated_at), decimals
