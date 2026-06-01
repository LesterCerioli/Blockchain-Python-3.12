from fastapi import Request

from ..application.quote_service import QuoteService


def get_quote_service(request: Request) -> QuoteService:
    return request.app.state.defi_quote_service
