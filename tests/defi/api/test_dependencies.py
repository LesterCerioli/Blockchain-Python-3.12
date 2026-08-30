"""Tests for DeFi FastAPI dependency providers (FEATURE 1.2.3)."""
from __future__ import annotations

from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.services.defi.api.dependencies import (
    get_current_wallet_session,
    get_defi_settings,
    get_market_provider,
    get_wallet_service,
)
from app.services.defi.domain.entities.wallet_session import WalletSession
from app.services.defi.infrastructure.config.settings import DeFiSettings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_session(
    wallet_address: str = "0xabcdef1234567890abcdef1234567890abcdef12",
    session_id: str = "test-session-abc123",
    chain_id: int = 1,
) -> WalletSession:
    return WalletSession(
        wallet_address=wallet_address,
        session_id=session_id,
        chain_id=chain_id,
    )


def _make_app(wallet_connector_mock) -> FastAPI:
    """Creates a minimal FastAPI app with app.state wired for testing."""
    app = FastAPI()
    app.state.defi_wallet_connector = wallet_connector_mock
    app.state.defi_market_provider = MagicMock()

    @app.get("/session")
    async def session_endpoint(
        session: WalletSession = Depends(get_current_wallet_session),
    ):
        return {"wallet_address": session.wallet_address, "chain_id": session.chain_id}

    return app


# ---------------------------------------------------------------------------
# get_defi_settings
# ---------------------------------------------------------------------------

class TestGetDefiSettings:
    def test_returns_defi_settings_instance(self):
        settings = get_defi_settings()
        assert isinstance(settings, DeFiSettings)

    def test_singleton_via_lru_cache(self):
        s1 = get_defi_settings()
        s2 = get_defi_settings()
        assert s1 is s2

    def test_has_expected_defaults(self):
        settings = get_defi_settings()
        assert settings.supported_chain_ids == [1, 137, 42161]
        assert settings.default_slippage_bps == 50


# ---------------------------------------------------------------------------
# get_market_provider
# ---------------------------------------------------------------------------

class TestGetMarketProvider:
    def test_returns_provider_from_app_state(self):
        mock_provider = MagicMock()
        app = FastAPI()
        app.state.defi_market_provider = mock_provider

        @app.get("/provider")
        def provider_endpoint(request_obj=None):
            from fastapi import Request
            return {}

        request = MagicMock()
        request.app.state.defi_market_provider = mock_provider

        result = get_market_provider(request)
        assert result is mock_provider

    def test_provider_is_the_same_object_stored_in_state(self):
        mock_provider = MagicMock()
        request = MagicMock()
        request.app.state.defi_market_provider = mock_provider

        assert get_market_provider(request) is mock_provider


# ---------------------------------------------------------------------------
# get_wallet_service
# ---------------------------------------------------------------------------

class TestGetWalletService:
    def test_returns_connector_from_app_state(self):
        mock_connector = MagicMock()
        request = MagicMock()
        request.app.state.defi_wallet_connector = mock_connector

        result = get_wallet_service(request)
        assert result is mock_connector

    def test_wallet_service_is_same_object_stored_in_state(self):
        mock_connector = MagicMock()
        request = MagicMock()
        request.app.state.defi_wallet_connector = mock_connector

        assert get_wallet_service(request) is mock_connector


# ---------------------------------------------------------------------------
# get_current_wallet_session
# ---------------------------------------------------------------------------

class TestGetCurrentWalletSession:
    def test_valid_session_returns_200_and_wallet_data(self):
        session = _make_session()
        mock_connector = MagicMock()
        mock_connector.get_session = AsyncMock(return_value=session)

        client = TestClient(_make_app(mock_connector))
        response = client.get("/session", headers={"X-Session-Id": "test-session-abc123"})

        assert response.status_code == 200
        data = response.json()
        assert data["wallet_address"] == session.wallet_address
        assert data["chain_id"] == 1

    def test_missing_header_returns_401(self):
        mock_connector = MagicMock()
        mock_connector.get_session = AsyncMock(return_value=None)

        client = TestClient(_make_app(mock_connector))
        response = client.get("/session")

        assert response.status_code == 401

    def test_invalid_session_id_returns_401(self):
        mock_connector = MagicMock()
        mock_connector.get_session = AsyncMock(return_value=None)

        client = TestClient(_make_app(mock_connector))
        response = client.get("/session", headers={"X-Session-Id": "nonexistent-id"})

        assert response.status_code == 401
        assert "session" in response.json()["detail"].lower()

    def test_session_response_never_contains_private_key(self):
        session = _make_session()
        mock_connector = MagicMock()
        mock_connector.get_session = AsyncMock(return_value=session)

        client = TestClient(_make_app(mock_connector))
        response = client.get("/session", headers={"X-Session-Id": "test-session-abc123"})

        assert response.status_code == 200
        body = response.text
        assert "private_key" not in body
        assert "privateKey" not in body
        assert "private" not in body

    def test_wallet_address_in_session_is_not_private_key_format(self):
        session = _make_session()
        mock_connector = MagicMock()
        mock_connector.get_session = AsyncMock(return_value=session)

        client = TestClient(_make_app(mock_connector))
        response = client.get("/session", headers={"X-Session-Id": "test-session-abc123"})

        wallet_address = response.json()["wallet_address"].lower().removeprefix("0x")
        assert len(wallet_address) != 64, "wallet_address must not look like a 32-byte private key"

    def test_connector_get_session_called_with_header_value(self):
        session = _make_session(session_id="my-sid-xyz")
        mock_connector = MagicMock()
        mock_connector.get_session = AsyncMock(return_value=session)

        client = TestClient(_make_app(mock_connector))
        client.get("/session", headers={"X-Session-Id": "my-sid-xyz"})

        mock_connector.get_session.assert_awaited_once_with("my-sid-xyz")

    def test_empty_string_session_id_returns_401(self):
        mock_connector = MagicMock()
        mock_connector.get_session = AsyncMock(return_value=None)

        client = TestClient(_make_app(mock_connector))
        response = client.get("/session", headers={"X-Session-Id": ""})

        assert response.status_code == 401
