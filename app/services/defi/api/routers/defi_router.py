from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_quote_service
from ..schemas.quote import QuoteRequest, QuoteResponse
from ...application.quote_service import QuoteService
from ...domain.exceptions import (
    DeFiError,
    NoPoolsForPairError,
    SlippageExceededError,
    TokenNotFoundError,
)
from ...domain.value_objects.slippage import Slippage

router = APIRouter(prefix="/v1/defi", tags=["defi"])


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
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except DeFiError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
