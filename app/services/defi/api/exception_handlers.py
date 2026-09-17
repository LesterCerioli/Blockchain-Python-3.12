from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from .schemas.common import ErrorResponse
from ..domain.exceptions import (
    DeFiError,
    IndexerLagError,
    InsufficientLiquidityError,
    InvalidAddressError,
    MarketDataError,
    NoPoolsForPairError,
    NonCustodialViolationError,
    PoolNotFoundError,
    PositionNotFoundError,
    PriceUnavailableError,
    ProtocolNotSupportedError,
    ProviderUnavailableError,
    RateLimitError,
    SanctionedAddressError,
    SlippageExceededError,
    TokenNotFoundError,
    ToUNotAcceptedError,
    WalletConnectionError,
)

# Maps concrete exception types to (HTTP status code, machine-readable error_code).
# Order matters: more specific types must come before their bases when the
# lookup iterates with isinstance checks, which is enforced by dict insertion order.
_EXCEPTION_STATUS_MAP: dict[type[DeFiError], tuple[int, str]] = {
    # 400 — Bad request (caller error, correctable)
    InvalidAddressError: (400, "INVALID_ADDRESS"),
    # 403 — Forbidden (compliance / policy)
    SanctionedAddressError: (403, "SANCTIONED_ADDRESS"),
    ToUNotAcceptedError: (403, "TOU_NOT_ACCEPTED"),
    NonCustodialViolationError: (403, "NON_CUSTODIAL_VIOLATION"),
    # 404 — Resource not found
    TokenNotFoundError: (404, "TOKEN_NOT_FOUND"),
    PoolNotFoundError: (404, "POOL_NOT_FOUND"),
    NoPoolsForPairError: (404, "NO_POOLS_FOR_PAIR"),
    PositionNotFoundError: (404, "POSITION_NOT_FOUND"),
    PriceUnavailableError: (404, "PRICE_UNAVAILABLE"),
    # 422 — Business rule / semantic validation failure
    SlippageExceededError: (422, "SLIPPAGE_EXCEEDED"),
    InsufficientLiquidityError: (422, "INSUFFICIENT_LIQUIDITY"),
    ProtocolNotSupportedError: (422, "PROTOCOL_NOT_SUPPORTED"),
    # 429 — Rate limited by upstream provider
    RateLimitError: (429, "RATE_LIMIT_EXCEEDED"),
    # 503 — Upstream unavailable / indexer lag
    ProviderUnavailableError: (503, "PROVIDER_UNAVAILABLE"),
    IndexerLagError: (503, "INDEXER_LAG"),
    # 502 — Generic upstream data failure
    MarketDataError: (502, "MARKET_DATA_ERROR"),
    # 400 — Generic wallet connectivity problem
    WalletConnectionError: (400, "WALLET_CONNECTION_ERROR"),
}


def _safe_details(exc: DeFiError) -> dict[str, Any] | None:
    """Extract domain-specific fields, stripping top-level keys already in ErrorResponse."""
    raw = exc.to_dict()
    raw.pop("error", None)
    raw.pop("message", None)
    return raw if raw else None


def _resolve(exc: DeFiError) -> tuple[int, str]:
    for exc_type, mapping in _EXCEPTION_STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return mapping
    return 500, "INTERNAL_DEFI_ERROR"


def _build_response(request: Request, exc: DeFiError) -> JSONResponse:
    status_code, error_code = _resolve(exc)
    request_id: str = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    body = ErrorResponse(
        error_code=error_code,
        message=str(exc),
        details=_safe_details(exc),
        request_id=request_id,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json"),
    )


async def defi_error_handler(request: Request, exc: DeFiError) -> JSONResponse:
    return _build_response(request, exc)


def register_defi_exception_handlers(app: Any) -> None:
    """Register all DeFi domain exception handlers on the FastAPI application."""
    app.add_exception_handler(DeFiError, defi_error_handler)
