from functools import lru_cache

from fastapi import Header, HTTPException, Request, status

from ..application.chain_config_service import ChainConfigService
from ..application.index_service import IndexService
from ..application.quote_service import QuoteService
from ..domain.entities.wallet_session import WalletSession
from ..domain.interfaces.ohlcv_repository import IOHLCVRepository
from ..domain.interfaces.wallet_connector import IWalletConnector
from ..infrastructure.config.settings import DeFiSettings
from ..infrastructure.compliance.in_memory_sanctions_screener import (
    InMemorySanctionsScreener,
)
from ..infrastructure.persistence.platform_secrets_service import PlatformSecretsService
from .middleware.sanctions_guard import SanctionsGuard


@lru_cache(maxsize=1)
def get_defi_settings() -> DeFiSettings:
    return DeFiSettings()


def get_market_provider(request: Request):
    return request.app.state.defi_market_provider


def get_wallet_service(request: Request) -> IWalletConnector:
    return request.app.state.defi_wallet_connector


def get_sanctions_guard(request: Request) -> SanctionsGuard:
    guard = getattr(request.app.state, "defi_sanctions_guard", None)
    if guard is None:
        guard = SanctionsGuard(InMemorySanctionsScreener(), enabled=False)
    return guard


async def enforce_sanctions_guard(request: Request) -> None:
    """Route dependency: screen the public address before session creation."""
    await get_sanctions_guard(request)(request)


async def get_current_wallet_session(
    request: Request,
    x_session_id: str | None = Header(default=None),  # noqa: B008
) -> WalletSession:
    if not x_session_id or not x_session_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session id. Send header X-Session-Id.",
        )
    connector = get_wallet_service(request)
    session = await connector.get_session(x_session_id.strip())
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired",
        )
    return session


def get_quote_service(request: Request) -> QuoteService:
    return request.app.state.defi_quote_service


def get_market_quote_service(request: Request) -> QuoteService:
    return request.app.state.defi_quote_service


def get_platform_secrets_service(request: Request) -> PlatformSecretsService:
    
    try:
        svc = request.app.state.platform_secrets_service
    except AttributeError:
        svc = None
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="platform_secrets_service not configured",
        )
    return svc


def get_chain_config_service(request: Request) -> ChainConfigService:
    
    try:
        svc = request.app.state.chain_config_service
    except AttributeError:
        svc = None
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="chain_config_service not configured",
        )
    return svc


def get_ohlcv_repository(request: Request) -> IOHLCVRepository:
    return request.app.state.defi_ohlcv_repository


def get_index_service(request: Request) -> IndexService:
    
    try:
        svc = request.app.state.index_service
    except AttributeError:
        svc = None
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="index_service not configured",
        )
    return svc
