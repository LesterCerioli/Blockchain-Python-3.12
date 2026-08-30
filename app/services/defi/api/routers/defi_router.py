from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ...application.index_service import IndexService
from ...application.quote_service import QuoteService
from ...domain.entities.index import (
    MarketIndex,
    PaginatedResponse,
    ProtocolRanking,
    TokenRanking,
)
from ...domain.exceptions import (
    DeFiError,
    IndexNotFoundError,
    InvalidOHLCVIntervalError,
    NoPoolsForPairError,
    OHLCVRangeExceededError,
    SlippageExceededError,
    TokenNotFoundError,
)
from ...domain.value_objects.slippage import Slippage
from ..dependencies import get_index_service, get_quote_service
from ..schemas.ohlcv import OHLCVCandle, OHLCVResponse
from ..schemas.quote import QuoteRequest, QuoteResponse


class IndexCode(BaseModel):
    code: str


router = APIRouter(prefix="/v1/defi", tags=["defi"])


@router.post(
    "/indexes",
    response_model=MarketIndex,
    summary="Get a market index by code",
)
async def get_index_by_code(
    index_code: IndexCode = Body(...),  # noqa: B008
    index_service: IndexService = Depends(get_index_service),  # noqa: B008
) -> MarketIndex:
    try:
        index = await index_service.get_index(index_code.code)
        return index
    except IndexNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DeFiError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.post(
    "/quote",
    response_model=QuoteResponse,
    summary="Get a swap quote for a token pair",
)
async def get_quote(
    body: QuoteRequest,
    quote_service: QuoteService = Depends(get_quote_service),  
) -> QuoteResponse:
    try:
        result = await quote_service.get_quote(
            token_in_address=body.token_in,
            token_out_address=body.token_out,
            amount_in_raw=body.amount_in_raw,
            chain_id=body.chain_id,
            slippage=Slippage(bps=body.slippage_bps),
        )
        return QuoteResponse(**result)
    except TokenNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except NoPoolsForPairError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except SlippageExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except DeFiError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.get(
    "/quotes/{symbol}/history",
    response_model=OHLCVResponse,
    summary="Get OHLCV history for a token symbol",
)
async def get_ohlcv_history(
    symbol: str,
    interval: str = Query(...),
    from_ts: datetime = Query(...),  # noqa: B008
    to_ts: datetime = Query(...),  # noqa: B008
    quote_service: QuoteService = Depends(get_quote_service),  # noqa: B008
) -> OHLCVResponse:
    try:
        candles = await quote_service.get_ohlcv(
            symbol=symbol,
            interval=interval,
            from_ts=from_ts,
            to_ts=to_ts,
        )
        return OHLCVResponse(
            symbol=symbol,
            interval=interval,
            candles=[
                OHLCVCandle(
                    open_time=c.open_time.isoformat(),
                    open=str(c.open),
                    high=str(c.high),
                    low=str(c.low),
                    close=str(c.close),
                    volume=str(c.volume),
                )
                for c in candles
            ],
        )
    except InvalidOHLCVIntervalError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except OHLCVRangeExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except DeFiError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.get(
    "/indexes",
    response_model=list[MarketIndex],
    tags=["Indexes"],
    summary="List available market indexes",
)
async def list_indices(
    code: str | None = Query(None),
    index_service: IndexService = Depends(get_index_service),  # noqa: B008
) -> list[MarketIndex]:
    try:
        if code:
            return [await index_service.get_index(code)]
        return await index_service.list_indices()
    except IndexNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DeFiError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


VALID_METRICS = ["market_cap", "volume_24h", "price_change_24h"]
SUPPORTED_CHAINS = ["ethereum", "bsc", "polygon", "avalanche", "fantom", "optimism", "arbitrum", "celo"]


@router.get(
    "/indexes/tokens/rankings",
    response_model=PaginatedResponse[TokenRanking],
    tags=["Indexes"],
    summary="Rank tokens by a metric (price/volume/market_cap proxy)",
)
async def token_rankings(
    metric: str = Query("market_cap"),
    chain: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    index_service: IndexService = Depends(get_index_service),  # noqa: B008
) -> PaginatedResponse[TokenRanking]:
    if metric not in VALID_METRICS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid metric. Valid: {', '.join(VALID_METRICS)}",
        )

    if chain is not None and chain.lower() not in [c.lower() for c in SUPPORTED_CHAINS]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported chain. Valid: {', '.join(SUPPORTED_CHAINS)}",
        )

    try:
        return await index_service.get_token_rankings(metric, chain, page, page_size)
    except DeFiError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.get(
    "/indexes/protocols/rankings",
    response_model=list[ProtocolRanking],
    tags=["Indexes"],
    summary="Rank protocols by TVL",
)
async def protocol_rankings(
    metric: str = Query("tvl"),
    chain_id: int | None = Query(None),
    index_service: IndexService = Depends(get_index_service),  # noqa: B008
) -> list[ProtocolRanking]:
    try:
        return await index_service.get_protocol_rankings(metric, chain_id)
    except DeFiError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
