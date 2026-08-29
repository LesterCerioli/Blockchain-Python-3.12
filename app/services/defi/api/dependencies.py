from fastapi import Request

from ..application.quote_service import QuoteService
from ..domain.interfaces.ohlcv_repository import IOHLCVRepository


def get_quote_service(request: Request) -> QuoteService:
    return request.app.state.defi_quote_service


def get_ohlcv_repository(request: Request) -> IOHLCVRepository:
    return request.app.state.defi_ohlcv_repository
