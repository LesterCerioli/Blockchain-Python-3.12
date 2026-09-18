from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.auth.api.dependencies import get_current_token
from app.services.defi.api.exception_handlers import (
    register_defi_exception_handlers,
)
from app.services.defi.api.routers.wallet_router import wallet_router
from app.services.defi.application.wallet_session_service import (
    WalletSessionService,
)
from app.services.defi.domain.exceptions import (
    InvalidAddressError,
    NonCustodialViolationError,
)

AJAX = "0x" + "a" * 40


class InMemoryRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def setex(self, key: str, seconds: int, value: str) -> None:
        self._store[key] = value

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0


def _make_client(svc: WalletSessionService) -> TestClient:
    app = FastAPI()
    register_defi_exception_handlers(app)
    app.state.defi_wallet_connector = svc
    app.dependency_overrides[get_current_token] = lambda: {
        "sub": "test",
        "iss": "auth_service",
        "type": "m2m",
    }
    app.include_router(wallet_router)
    return TestClient(app)


@pytest.fixture
def client() -> TestClient:
    svc = WalletSessionService(InMemoryRedis())
    return _make_client(svc)


class TestConnectEndpoint:

    def test_connect_returns_session_and_is_reusable(self, client: TestClient):
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": "0xAbCd" + "a" * 36, "chain_id": 1},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["wallet_address"] == "0xabcd" + "a" * 36
        assert data["chain_id"] == 1
        assert data["session_id"]

        session_id = data["session_id"]
        check = client.get("/wallet/session", headers={"X-Session-Id": session_id})
        assert check.status_code == 200
        assert check.json()["wallet_address"] == "0xabcd" + "a" * 36

    def test_connect_invalid_address_returns_400(self, client: TestClient):
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": "not-an-address", "chain_id": 1},
        )
        assert resp.status_code == 400
        assert resp.json()["error_code"] == "INVALID_ADDRESS"

    def test_connect_private_key_shaped_returns_403(self, client: TestClient):
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": "0x" + "b" * 64, "chain_id": 1},
        )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "NON_CUSTODIAL_VIOLATION"

    def test_connect_chain_id_zero_is_rejected(self, client: TestClient):
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": AJAX, "chain_id": 0},
        )
        assert resp.status_code == 422


class TestGetSessionEndpoint:

    def test_missing_session_header_returns_401(self, client: TestClient):
        resp = client.get("/wallet/session")
        assert resp.status_code == 401

    def test_unknown_session_returns_401(self, client: TestClient):
        resp = client.get(
            "/wallet/session",
            headers={"X-Session-Id": "00000000-0000-0000-0000-000000000000"},
        )
        assert resp.status_code == 401

    def test_empty_header_returns_401(self, client: TestClient):
        resp = client.get("/wallet/session", headers={"X-Session-Id": ""})
        assert resp.status_code == 401


class TestDisconnectEndpoint:

    def test_disconnect_revokes_session(self, client: TestClient):
        connect = client.post(
            "/wallet/connect",
            json={"wallet_address": AJAX, "chain_id": 1},
        ).json()
        session_id = connect["session_id"]

        resp = client.delete(
            "/wallet/session", headers={"X-Session-Id": session_id}
        )
        assert resp.status_code == 200
        assert resp.json()["detail"] == "session revoked"

        after = client.get("/wallet/session", headers={"X-Session-Id": session_id})
        assert after.status_code == 401

    def test_disconnect_never_exposes_key_data(self, client: TestClient):
        connect = client.post(
            "/wallet/connect",
            json={"wallet_address": AJAX, "chain_id": 1},
        ).json()
        session_id = connect["session_id"]
        resp = client.delete(
            "/wallet/session", headers={"X-Session-Id": session_id}
        )
        body = resp.text.lower()
        assert "private_key" not in body
        assert "private" not in body