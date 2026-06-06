from fastapi import APIRouter

from .admin_router import admin_router
from .chains_router import chains_router
from .quotes_router import quotes_router
from .wallet_router import wallet_router
from .research_router import research_router
from .portfolio_router import portfolio_router
from ..schemas.common import HealthResponse, HealthStatus

defi_router = APIRouter(prefix="/api/v1/defi", tags=["DeFi"])


@defi_router.get(
    "/health",
    response_model=HealthResponse,
    summary="DeFi service health check",
)
async def defi_health() -> HealthResponse:
    return HealthResponse(status=HealthStatus.OK)


defi_router.include_router(chains_router)
defi_router.include_router(quotes_router)
defi_router.include_router(wallet_router)
defi_router.include_router(research_router)
defi_router.include_router(portfolio_router)
defi_router.include_router(admin_router)

__all__ = ["defi_router"]
