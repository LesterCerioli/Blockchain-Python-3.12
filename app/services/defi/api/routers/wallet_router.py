from fastapi import APIRouter, Depends

from app.services.auth.api.dependencies import get_current_token

wallet_router = APIRouter(
    prefix="/wallet",
    tags=["DeFi – Wallet"],
    dependencies=[Depends(get_current_token)],
)
