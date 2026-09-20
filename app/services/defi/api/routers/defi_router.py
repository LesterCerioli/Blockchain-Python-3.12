from fastapi import APIRouter

from .market_router import market_router
from .wallet_router import wallet_router


router = APIRouter(prefix="/v1/defi", tags=["defi"])
router.include_router(wallet_router)
router.include_router(market_router)