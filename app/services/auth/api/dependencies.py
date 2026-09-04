from __future__ import annotations

import os

import jwt
from dotenv import load_dotenv
from fastapi import Header, HTTPException, Request, status

load_dotenv()

_public_key = os.getenv("PUBLIC_KEY_VALUE")


async def get_current_token(
    request: Request,
    authorization: str | None = Header(
        default=None,
        description="JWT de uso único gerado em POST /auth/token. Formato: Bearer <token>. Gere um novo token a cada request.",
    ),
) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Informe o header Authorization: Bearer <token gerado em POST /auth/token>.",
        )
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Token vazio no header Authorization.",
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

    # Single-use enforcement: token must exist in DB and is revoked after first use.
    # When there is no AuthService (unit tests that call the dependency directly
    # or routers mounted without lifespan), fall back to signature-only validation
    # to keep backward compatibility.
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

    # Consume the token so it cannot be reused in another request.
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
