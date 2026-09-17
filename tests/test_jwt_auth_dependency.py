import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


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


@pytest.fixture(autouse=True)
def mock_public_key():
    with patch("app.services.auth.api.dependencies._public_key", PUBLIC_KEY):
        yield


from app.services.auth.api.dependencies import get_current_token


def _bearer(token: str) -> str:
    return f"Bearer {token}"


def _make_token(**claims) -> str:
    payload = {"sub": "client123", "iss": "auth_service", "type": "m2m"}
    payload.update(claims)
    return jwt.encode(payload, PRIVATE_KEY, algorithm="EdDSA")


class TestGetCurrentToken:
    def test_valid_token_returns_payload(self):
        payload = asyncio.run(get_current_token(None, _bearer(_make_token())))
        assert payload["sub"] == "client123"
        assert payload["iss"] == "auth_service"
        assert payload["type"] == "m2m"

    def test_missing_header_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_token(None, None))
        assert exc_info.value.status_code == 401

    def test_malformed_header_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_token(None, "Token abc123"))
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_token(None, _bearer(_make_token(exp=0))))
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_token(None, _bearer("invalid.token.value")))
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail

    def test_wrong_issuer_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_token(None, _bearer(_make_token(iss="wrong_issuer"))))
        assert exc_info.value.status_code == 401

    def test_wrong_algorithm_raises_401(self):
        token = jwt.encode(
            {
                "sub": "client123",
                "iss": "auth_service",
            },
            "secret",
            algorithm="HS256",
        )
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_token(None, _bearer(token)))
        assert exc_info.value.status_code == 401

    def test_single_use_token_reuse_raises_401(self):
        token = _make_token()
        mock_service = MagicMock()
        mock_service.validate_token = AsyncMock(return_value={"valid": True})
        # First use consumes the token, second use finds it already consumed.
        mock_service.revoke_token = AsyncMock(side_effect=[True, False])
        mock_request = MagicMock()
        mock_request.app.state.auth_service = mock_service

        payload = asyncio.run(get_current_token(mock_request, _bearer(token)))
        assert payload["sub"] == "client123"
        assert mock_service.validate_token.await_count == 1
        assert mock_service.revoke_token.await_count == 1

        # Reuse with a service where the token no longer exists.
        mock_service2 = MagicMock()
        mock_service2.validate_token = AsyncMock(
            side_effect=ValueError("Token not found in database")
        )
        mock_request2 = MagicMock()
        mock_request2.app.state.auth_service = mock_service2
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_token(mock_request2, _bearer(token)))
        assert exc_info.value.status_code == 401
        assert "already been used" in exc_info.value.detail.lower()

    def test_reused_token_second_call_fails_when_revoke_returns_false(self):
        mock_service = MagicMock()
        mock_service.validate_token = AsyncMock(return_value={"valid": True})
        mock_service.revoke_token = AsyncMock(return_value=False)
        mock_request = MagicMock()
        mock_request.app.state.auth_service = mock_service
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_token(mock_request, _bearer(_make_token())))
        assert exc_info.value.status_code == 401
