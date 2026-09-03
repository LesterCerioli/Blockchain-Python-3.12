import os
import sys
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

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


class TestGetCurrentToken:
    def test_valid_token_returns_payload(self):
        token = jwt.encode(
            {
                "sub": "client123",
                "iss": "auth_service",
                "type": "m2m",
            },
            PRIVATE_KEY,
            algorithm="EdDSA",
        )
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        payload = get_current_token(creds)
        assert payload["sub"] == "client123"
        assert payload["iss"] == "auth_service"
        assert payload["type"] == "m2m"

    def test_expired_token_raises_401(self):
        token = jwt.encode(
            {
                "sub": "client123",
                "iss": "auth_service",
                "exp": 0,
            },
            PRIVATE_KEY,
            algorithm="EdDSA",
        )
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc_info:
            get_current_token(creds)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_invalid_token_raises_401(self):
        creds = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid.token.value"
        )
        with pytest.raises(HTTPException) as exc_info:
            get_current_token(creds)
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail

    def test_wrong_issuer_raises_401(self):
        token = jwt.encode(
            {
                "sub": "client123",
                "iss": "wrong_issuer",
            },
            PRIVATE_KEY,
            algorithm="EdDSA",
        )
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc_info:
            get_current_token(creds)
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
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc_info:
            get_current_token(creds)
        assert exc_info.value.status_code == 401
