from fastapi import APIRouter, Depends

from app.services.auth.api.dependencies import get_current_token

research_router = APIRouter(
    prefix="/research",
    tags=["DeFi – Research"],
    dependencies=[Depends(get_current_token)],
)
