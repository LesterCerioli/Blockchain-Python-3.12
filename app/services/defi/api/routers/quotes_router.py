from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import get_market_quote_service, get_quote_service
from ..schemas.quote import CandleResponse, MarketQuoteResponse, OHLCVResponse, QuoteRequest, QuoteResponse
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


_MAX_BATCH_SYMBOLS = 50


@quotes_router.get(
    "",
    response_model=list[MarketQuoteResponse],
    summary="Get spot market quotes for multiple cryptocurrency symbols",
)
async def get_market_quotes(
    symbols: str = Query(
        ...,
        description="Comma-separated list of symbols (max 50)",
    ),
    market_quote_service: QuoteService = Depends(get_market_quote_service),
) -> list[MarketQuoteResponse]:
    raw = [s.strip() for s in symbols.split(",") if s.strip()]

    if len(raw) > _MAX_BATCH_SYMBOLS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Too many symbols: {len(raw)}. Maximum is {_MAX_BATCH_SYMBOLS}.",
        )

    quotes = await market_quote_service.get_market_quotes(symbols)

    return [
        MarketQuoteResponse(
            symbol=q.symbol,
            price_usd=str(q.price_usd),
            change_24h_pct=float(q.change_24h) if q.change_24h is not None else 0.0,
            volume_24h_usd=str(q.volume_24h),
            market_cap_usd=str(q.market_cap),
            fetched_at=q.fetched_at,
        )
        for q in quotes
    ]


_VALID_INTERVALS = {"1m", "5m", "15m", "1h", "4h", "1d", "1w"}
_MAX_HISTORY_DAYS = 365


@quotes_router.get(
    "/{symbol}/history",
    response_model=OHLCVResponse,
    summary="Get historical OHLCV candles for a cryptocurrency symbol",
)
async def get_ohlcv_history(
    symbol: str,
    interval: str = Query(
        ...,
        description="Candle interval: 1m, 5m, 15m, 1h, 4h, 1d, 1w",
    ),
    from_: datetime = Query(
        ...,
        alias="from",
        description="Start of the range (ISO 8601)",
    ),
    to: datetime = Query(
        ...,
        description="End of the range (ISO 8601)",
    ),
    market_quote_service: QuoteService = Depends(get_market_quote_service),
) -> OHLCVResponse:
    if interval not in _VALID_INTERVALS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid interval: {interval}. Valid intervals: {', '.join(sorted(_VALID_INTERVALS))}.",
        )

    delta = to - from_
    if delta.days > _MAX_HISTORY_DAYS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Date range exceeds {_MAX_HISTORY_DAYS} days ({delta.days} days requested).",
        )

    candles = await market_quote_service.get_ohlcv(symbol, interval, from_, to)

    return OHLCVResponse(
        symbol=symbol.upper(),
        interval=interval,
        candles=[
            CandleResponse(
                open_time=c.timestamp,
                open=str(c.open),
                high=str(c.high),
                low=str(c.low),
                close=str(c.close),
                volume="0",
            )
            for c in candles
        ],
    )
