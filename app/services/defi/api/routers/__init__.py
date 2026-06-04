from fastapi import APIRouter

from .quotes_router import quotes_router
from .wallet_router import wallet_router
from .research_router import research_router
from .portfolio_router import portfolio_router

defi_router = APIRouter(prefix="/api/v1/defi", tags=["DeFi"])


@defi_router.get("/health", summary="DeFi service health check")
async def defi_health():
    return {"status": "ok"}


defi_router.include_router(quotes_router)
defi_router.include_router(wallet_router)
defi_router.include_router(research_router)
defi_router.include_router(portfolio_router)

__all__ = ["defi_router"]
