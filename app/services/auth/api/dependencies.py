from __future__ import annotations

import os

import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, Query, Request, status

load_dotenv()

_public_key = os.getenv("PUBLIC_KEY_VALUE")


def _extract_token(authorization: str | None) -> str | None:
    """Extract the raw JWT from the REQUIRED ``authorization`` query parameter.

    Accepts either ``Bearer <token>`` or the raw token returned by
    ``POST /auth/token`` (``access_token``). The ``authorization`` header is
    intentionally not read: the query parameter is the single authentication
    channel for every protected endpoint.
    """
    if not isinstance(authorization, str):
        return None
    value = authorization.strip()
    if value.lower().startswith("bearer "):
        value = value[7:]
    return value.strip() or None


async def get_current_token(
    request: Request,
    authorization: str | None = Query(
        ...,
        description="Token JWT gerado em POST /auth/token (campo access_token), enviado como query parameter. Campo obrigatório para todos os endpoints, exceto POST /auth/token e /auth/token/validate.",
    ),
) -> dict:
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Not authenticated. Informe o query parameter authorization=<token> "
                "com o token gerado em POST /auth/token."
            ),
        )
    try:
        payload = jwt.decode(
            token,
            _public_key,
            algorithms=["EdDSA"],
            issuer="auth_service",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )

    
    auth_service = None
    if request is not None:
        try:
            auth_service = request.app.state.auth_service
        except Exception:
            auth_service = None

    if auth_service is None:
        return payload

    try:
        await auth_service.validate_token(jwt_token=token)
    except ValueError as exc:
        detail = str(exc)
        if "expired" in detail.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        if "not found" in detail.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has already been used or is unknown. Generate a new token via POST /auth/token.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )

    
    try:
        revoked = await auth_service.revoke_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has already been used. Generate a new token via POST /auth/token.",
        )

    return payload
