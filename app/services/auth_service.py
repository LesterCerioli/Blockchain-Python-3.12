from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import asyncpg
import jwt
from dotenv import load_dotenv
from jwt import PyJWKClient

load_dotenv()

TOKEN_TTL_SECONDS = 120


class AuthService:

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: Optional[asyncpg.Pool] = None
        self._client_id = os.getenv("CLIENT_ID")
        self._client_secret = os.getenv("CLIENT_SECRET")
        self._private_key = os.getenv("PRIVATE_KEY_VALUE")
        self._public_key = os.getenv("PUBLIC_KEY_VALUE")

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=5)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def ensure_table(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS public.auth_tokens (
            id          UUID                        PRIMARY KEY DEFAULT gen_random_uuid(),
            client_id   VARCHAR(64)                 NOT NULL,
            jwt_token   TEXT                        NOT NULL,
            created_at  TIMESTAMP WITH TIME ZONE    NOT NULL DEFAULT NOW(),
            expires_at  TIMESTAMP WITH TIME ZONE    NOT NULL
        );
        """
        async with self._pool.acquire() as conn:
            await conn.execute(ddl)

    def _authenticate_credentials(self, client_id: str, client_secret: str) -> bool:
        import hmac
        return hmac.compare_digest(client_id, self._client_id) and hmac.compare_digest(
            client_secret, self._client_secret
        )

    def _create_jwt(self, client_id: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": client_id,
            "iat": now,
            "exp": now + timedelta(seconds=TOKEN_TTL_SECONDS),
            "iss": "auth_service",
            "type": "m2m",
        }
        return jwt.encode(payload, self._private_key, algorithm="EdDSA")

    def _verify_jwt(self, token: str) -> dict:
        return jwt.decode(
            token,
            self._public_key,
            algorithms=["EdDSA"],
            issuer="auth_service",
        )

    async def generate_token(self, client_id: str, client_secret: str) -> dict:
        if not self._authenticate_credentials(client_id, client_secret):
            raise PermissionError("Invalid client_id or client_secret")

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=TOKEN_TTL_SECONDS)
        token_id = uuid4()

        jwt_token = self._create_jwt(client_id)

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.auth_tokens (id, client_id, jwt_token, created_at, expires_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                token_id,
                client_id,
                jwt_token,
                now,
                expires_at,
            )

        return {
            "access_token": jwt_token,
            "token_type": "Bearer",
            "expires_in": TOKEN_TTL_SECONDS,
            "expires_at": expires_at.isoformat(),
        }

    async def validate_token(self, jwt_token: str) -> dict:
        try:
            payload = self._verify_jwt(jwt_token)
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as exc:
            raise ValueError(f"Invalid token: {exc}")

        client_id = payload.get("sub")

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, client_id, expires_at
                FROM public.auth_tokens
                WHERE jwt_token = $1 AND client_id = $2
                ORDER BY created_at DESC
                LIMIT 1
                """,
                jwt_token,
                client_id,
            )

        if row is None:
            raise ValueError("Token not found in database")

        if row["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise ValueError("Token has expired in database")

        return {
            "valid": True,
            "client_id": row["client_id"],
            "token_id": str(row["id"]),
            "expires_at": row["expires_at"].isoformat(),
        }

    async def revoke_token(self, jwt_token: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM public.auth_tokens WHERE jwt_token = $1",
                jwt_token,
            )
        deleted = int(result.split()[-1])
        return deleted > 0
