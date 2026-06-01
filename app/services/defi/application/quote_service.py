from decimal import ROUND_HALF_UP, Decimal

from ..domain.exceptions import (
    NoPoolsForPairError,
    SlippageExceededError,
    TokenNotFoundError,
)
from ..domain.interfaces.pool_repository import IPoolRepository
from ..domain.interfaces.price_oracle import IPriceOracle
from ..domain.interfaces.swap_service import ISwapService
from ..domain.interfaces.token_repository import ITokenRepository
from ..domain.value_objects.slippage import Slippage
from ..domain.value_objects.token_amount import TokenAmount


class QuoteService:
    
    def __init__(
        self,
        token_repository: ITokenRepository,
        pool_repository: IPoolRepository,
        price_oracle: IPriceOracle,
        swap_service: ISwapService,
    ) -> None:
        self._tokens = token_repository
        self._pools = pool_repository
        self._oracle = price_oracle
        self._swap = swap_service

    async def get_quote(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in_raw: int,
        chain_id: int,
        slippage: Slippage,
    ) -> dict:
        token_in = await self._tokens.get_by_address(token_in_address, chain_id)
        if token_in is None:
            raise TokenNotFoundError(token_in_address, chain_id)

        token_out = await self._tokens.get_by_address(token_out_address, chain_id)
        if token_out is None:
            raise TokenNotFoundError(token_out_address, chain_id)

        pools = await self._pools.list_by_tokens(token_in_address, token_out_address, chain_id)
        if not pools:
            raise NoPoolsForPairError(token_in_address, token_out_address, chain_id)

        amount_in = TokenAmount(
            raw=amount_in_raw,
            decimals=token_in.decimals,
            token_address=token_in_address,
        )
        amount_out = await self._swap.get_quote(
            token_in_address, token_out_address, amount_in, chain_id
        )

        price_impact = await self._calculate_price_impact(
            token_in_address, token_out_address, amount_in, amount_out, chain_id
        )

        actual_bps = int(
            Decimal(str(price_impact))
            .scaleb(4)
            .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        if actual_bps > slippage.bps:
            raise SlippageExceededError(expected_bps=slippage.bps, actual_bps=actual_bps)

        return {
            "token_in": token_in_address,
            "token_out": token_out_address,
            "amount_in": str(amount_in.as_decimal),
            "amount_out": str(amount_out.as_decimal),
            "price_impact_bps": actual_bps,
            "slippage_bps": slippage.bps,
            "pool_count": len(pools),
        }

    async def _calculate_price_impact(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: TokenAmount,
        amount_out: TokenAmount,
        chain_id: int,
    ) -> Decimal:
        spot = await self._oracle.get_price(token_in_address, token_out_address, chain_id)
        if spot is None or spot.value == 0:
            return Decimal(0)
        expected_out = amount_in.as_decimal * spot.value
        if expected_out == 0:
            return Decimal(0)
        return abs(expected_out - amount_out.as_decimal) / expected_out
