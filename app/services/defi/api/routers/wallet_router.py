from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, status

from app.services.auth.api.dependencies import get_current_token

from ...application.wallet_session_service import SESSION_TTL_SECONDS
from ...domain.entities.wallet_session import WalletSession
from ..dependencies import (
    enforce_sanctions_guard,
    get_current_wallet_session,
    get_wallet_service,
)
from ..schemas.wallet import (
    WalletConnectRequest,
    WalletConnectResponse,
    WalletDisconnectResponse,
)

wallet_router = APIRouter(
    prefix="/wallet",
    tags=["DeFi – Wallet"],
    dependencies=[Depends(get_current_token)],
)


@wallet_router.post(
    "/connect",
    response_model=WalletConnectResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(enforce_sanctions_guard)],
    summary="Connect a client wallet (public address only, never a private key)",
)
async def connect_wallet(
    body: WalletConnectRequest,
    wallet_service=Depends(get_wallet_service),  # noqa: B008
) -> WalletConnectResponse:
    session = await wallet_service.connect(
        wallet_address=body.wallet_address,
        chain_id=body.chain_id,
    )
    ttl = getattr(wallet_service, "session_ttl_seconds", SESSION_TTL_SECONDS)
    return WalletConnectResponse(
        session_token=session.session_id,
        wallet_address=session.wallet_address,
        chain_id=session.chain_id,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(seconds=ttl),
    )


@wallet_router.get(
    "/session",
    response_model=WalletSession,
    summary="Resolve the current wallet session from X-Session-Id",
)
async def get_current_session(
    session: WalletSession = Depends(get_current_wallet_session),  # noqa: B008
) -> WalletSession:
    return session


@wallet_router.delete(
    "/session",
    status_code=status.HTTP_200_OK,
    response_model=WalletDisconnectResponse,
    summary="Disconnect (revoke) a wallet session",
)
async def disconnect_wallet(
    session: WalletSession = Depends(get_current_wallet_session),  # noqa: B008
    wallet_service=Depends(get_wallet_service),  # noqa: B008
) -> WalletDisconnectResponse:
    await wallet_service.disconnect(session.session_id)
    return WalletDisconnectResponse()