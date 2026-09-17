from decimal import Decimal

from app.services.defi.domain.interfaces.swap_service import ISwapService
from app.services.defi.domain.value_objects.slippage import Slippage
from app.services.defi.domain.value_objects.token_amount import TokenAmount


class InMemorySwapService(ISwapService):
    async def get_quote(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: TokenAmount,
        chain_id: int,
    ) -> TokenAmount:

        fee_bps = 30
        amount_in_decimal = amount_in.as_decimal
        amount_out_decimal = amount_in_decimal * (
            Decimal(1) - Decimal(fee_bps) / Decimal(10_000)
        )
        raw_out = int(amount_out_decimal * Decimal(10**amount_in.decimals))
        return TokenAmount(
            raw=raw_out,
            decimals=amount_in.decimals,
            token_address=token_in_address,
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

        import uuid

        return str(uuid.uuid4())
