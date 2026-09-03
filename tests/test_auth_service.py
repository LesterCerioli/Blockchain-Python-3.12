import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.auth_service import AuthService, TOKEN_TTL_SECONDS


def _generate_keypair():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


PRIVATE_KEY, PUBLIC_KEY = _generate_keypair()


class FakePoolConnection:
    def __init__(self, store: dict):
        self._store = store

    async def execute(self, query, *args):
        if "INSERT" in query:
            self._store[args[1]] = {
                "id": args[0],
                "client_id": args[1],
                "jwt_token": args[2],
                "created_at": args[3],
                "expires_at": args[4],
            }
            return "INSERT 0 1"
        if "DELETE" in query:
            token = args[0]
            to_delete = [k for k, v in self._store.items() if v["jwt_token"] == token]
            for k in to_delete:
                del self._store[k]
            return f"DELETE {len(to_delete)}"
        return ""

    async def fetchrow(self, query, *args):
        if "SELECT" in query:
            token = args[0]
            client_id = args[1]
            for row in self._store.values():
                if row["jwt_token"] == token and row["client_id"] == client_id:
                    return row
        return None


class FakePool:
    def __init__(self):
        self._store: dict = {}

    def acquire(self):
        return self

    async def __aenter__(self):
        return FakePoolConnection(self._store)

    async def __aexit__(self, *args):
        pass


@pytest.fixture
def auth_service():
    service = AuthService(dsn="postgresql://fake:fake@localhost/fake")
    service._client_id = "test_client_id"
    service._client_secret = "test_client_secret_hex_32_bytes_long!"
    service._private_key = PRIVATE_KEY
    service._public_key = PUBLIC_KEY
    service._pool = FakePool()
    return service


class TestGenerateToken:
    def test_valid_credentials_returns_token(self, auth_service: AuthService):
        result = asyncio.run(auth_service.generate_token(
            client_id="test_client_id",
            client_secret="test_client_secret_hex_32_bytes_long!",
        ))
        assert "access_token" in result
        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == TOKEN_TTL_SECONDS
        assert "expires_at" in result

    def test_invalid_credentials_raises(self, auth_service: AuthService):
        with pytest.raises(PermissionError):
            asyncio.run(auth_service.generate_token(
                client_id="wrong",
                client_secret="wrong",
            ))

    def test_token_is_valid_jwt(self, auth_service: AuthService):
        result = asyncio.run(auth_service.generate_token(
            client_id="test_client_id",
            client_secret="test_client_secret_hex_32_bytes_long!",
        ))
        payload = jwt.decode(
            result["access_token"],
            PUBLIC_KEY,
            algorithms=["EdDSA"],
            issuer="auth_service",
        )
        assert payload["sub"] == "test_client_id"
        assert payload["type"] == "m2m"

    def test_token_stored_in_database(self, auth_service: AuthService):
        asyncio.run(auth_service.generate_token(
            client_id="test_client_id",
            client_secret="test_client_secret_hex_32_bytes_long!",
        ))
        assert len(auth_service._pool._store) == 1


class TestValidateToken:
    def test_valid_token(self, auth_service: AuthService):
        result = asyncio.run(auth_service.generate_token(
            client_id="test_client_id",
            client_secret="test_client_secret_hex_32_bytes_long!",
        ))
        valid = asyncio.run(auth_service.validate_token(result["access_token"]))
        assert valid["valid"] is True
        assert valid["client_id"] == "test_client_id"
        assert "token_id" in valid

    def test_invalid_token_raises(self, auth_service: AuthService):
        with pytest.raises(ValueError, match="Invalid token"):
            asyncio.run(auth_service.validate_token("invalid.token.here"))

    def test_token_not_in_db_raises(self, auth_service: AuthService):
        token = jwt.encode(
            {"sub": "test_client_id", "iss": "auth_service", "type": "m2m"},
            PRIVATE_KEY,
            algorithm="EdDSA",
        )
        with pytest.raises(ValueError, match="Token not found"):
            asyncio.run(auth_service.validate_token(token))


class TestRevokeToken:
    def test_revoke_existing_token(self, auth_service: AuthService):
        result = asyncio.run(auth_service.generate_token(
            client_id="test_client_id",
            client_secret="test_client_secret_hex_32_bytes_long!",
        ))
        revoked = asyncio.run(auth_service.revoke_token(result["access_token"]))
        assert revoked is True
        assert len(auth_service._pool._store) == 0

    def test_revoke_nonexistent_token(self, auth_service: AuthService):
        revoked = asyncio.run(auth_service.revoke_token("nonexistent"))
        assert revoked is False


class TestTokenExpiration:
    def test_token_ttl_is_120_seconds(self):
        assert TOKEN_TTL_SECONDS == 120
