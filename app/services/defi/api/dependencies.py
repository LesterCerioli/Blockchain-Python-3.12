from fastapi import HTTPException, Request, status

from ..application.chain_config_service import ChainConfigService
from ..application.index_service import IndexService
from ..application.quote_service import QuoteService
from ..domain.interfaces.ohlcv_repository import IOHLCVRepository
from ..infrastructure.persistence.platform_secrets_service import PlatformSecretsService


def get_quote_service(request: Request) -> QuoteService:
    return request.app.state.defi_quote_service


def get_market_quote_service(request: Request) -> QuoteService:
    return request.app.state.defi_quote_service


def get_platform_secrets_service(request: Request) -> PlatformSecretsService:
    """Resolve via lifespan (app.state). Nenhum client externo é criado aqui."""
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
    """Resolve via lifespan (app.state). Nenhum serviço é construído aqui."""
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
    """Resolve via lifespan (app.state). Nenhum client externo é criado aqui."""
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
