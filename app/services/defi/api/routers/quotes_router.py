from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_market_quote_service, get_quote_service
from ..schemas.quote import MarketQuoteResponse, QuoteRequest, QuoteResponse
from ...application.quote_service import QuoteService, SwapQuoteService
from ...domain.value_objects.slippage import Slippage

quotes_router = APIRouter(prefix="/quotes", tags=["DeFi – Quotes"])


@quotes_router.post(
    "",
    response_model=QuoteResponse,
    summary="Get a swap quote for a token pair",
)
async def get_quote(
    body: QuoteRequest,
    quote_service: SwapQuoteService = Depends(get_quote_service),
) -> QuoteResponse:
    result = await quote_service.get_quote(
        token_in_address=body.token_in,
        token_out_address=body.token_out,
        amount_in_raw=body.amount_in_raw,
        chain_id=body.chain_id,
        slippage=Slippage(bps=body.slippage_bps),
    )
    return QuoteResponse(**result)


@quotes_router.get(
    "/{symbol}",
    response_model=MarketQuoteResponse,
    summary="Get a spot market quote for a cryptocurrency symbol",
)
async def get_market_quote(
    symbol: str,
    market_quote_service: QuoteService = Depends(get_market_quote_service),
) -> MarketQuoteResponse:
    quote = await market_quote_service.get_quote(symbol)

    if quote.price_usd == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol not found: {symbol.upper()}",
        )

    return MarketQuoteResponse(
        symbol=quote.symbol,
        price_usd=str(quote.price_usd),
        change_24h_pct=float(quote.change_24h) if quote.change_24h is not None else 0.0,
        volume_24h_usd=str(quote.volume_24h),
        market_cap_usd=str(quote.market_cap),
        fetched_at=quote.fetched_at,
    )
