from fastapi import APIRouter, Depends

from ..dependencies import get_quote_service
from ..schemas.quote import QuoteRequest, QuoteResponse
from ...application.quote_service import QuoteService
from ...domain.value_objects.slippage import Slippage

quotes_router = APIRouter(prefix="/quotes", tags=["DeFi – Quotes"])


@quotes_router.post(
    "",
    response_model=QuoteResponse,
    summary="Get a swap quote for a token pair",
)
async def get_quote(
    body: QuoteRequest,
    quote_service: QuoteService = Depends(get_quote_service),
) -> QuoteResponse:
    result = await quote_service.get_quote(
        token_in_address=body.token_in,
        token_out_address=body.token_out,
        amount_in_raw=body.amount_in_raw,
        chain_id=body.chain_id,
        slippage=Slippage(bps=body.slippage_bps),
    )
    return QuoteResponse(**result)
