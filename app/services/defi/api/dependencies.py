from functools import lru_cache
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from ..application.quote_service import QuoteService
from ..domain.entities.wallet_session import WalletSession
from ..domain.interfaces.market_data_provider import IMarketDataProvider
from ..domain.interfaces.wallet_connector import IWalletConnector
from ..infrastructure.config.settings import DeFiSettings


@lru_cache
def get_defi_settings() -> DeFiSettings:
    return DeFiSettings()


def get_market_provider(request: Request) -> IMarketDataProvider:
    return request.app.state.defi_market_provider


def get_wallet_service(request: Request) -> IWalletConnector:
    return request.app.state.defi_wallet_connector


async def get_current_wallet_session(
    x_session_id: Annotated[Optional[str], Header()] = None,
    wallet_service: IWalletConnector = Depends(get_wallet_service),
) -> WalletSession:
    if not x_session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Session-Id header",
        )
    session = await wallet_service.get_session(x_session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    return session


def get_quote_service(request: Request) -> QuoteService:
    return request.app.state.defi_quote_service
