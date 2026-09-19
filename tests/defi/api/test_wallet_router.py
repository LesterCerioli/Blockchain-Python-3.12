from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.auth.api.dependencies import get_current_token
from app.services.defi.api.exception_handlers import (
    register_defi_exception_handlers,
)
from app.services.defi.api.middleware.sanctions_guard import SanctionsGuard
from app.services.defi.api.routers.wallet_router import wallet_router
from app.services.defi.application.wallet_session_service import (
    WalletSessionService,
)
from app.services.defi.domain.exceptions import (
    InvalidAddressError,
    NonCustodialViolationError,
)
from app.services.defi.infrastructure.compliance.in_memory_sanctions_screener import (
    InMemorySanctionsScreener,
)

AJAX = "0x" + "a" * 40
SANCTIONED = "0x" + "d" * 40


class InMemoryRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def setex(self, key: str, seconds: int, value: str) -> None:
        self._store[key] = value

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0


def _make_client(
    svc: WalletSessionService,
    guard: SanctionsGuard | None = None,
) -> TestClient:
    app = FastAPI()
    register_defi_exception_handlers(app)
    app.state.defi_wallet_connector = svc
    app.state.defi_sanctions_guard = guard or SanctionsGuard(
        InMemorySanctionsScreener(), enabled=False
    )
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
        assert resp.status_code == 200
        data = resp.json()
        assert data["wallet_address"] == "0xabcd" + "a" * 36
        assert data["chain_id"] == 1
        assert data["session_token"]
        assert data["expires_at"]

        session_id = data["session_token"]
        check = client.get("/wallet/session", headers={"X-Session-Id": session_id})
        assert check.status_code == 200
        assert check.json()["wallet_address"] == "0xabcd" + "a" * 36

    def test_connect_response_never_contains_private_key_contract(self, client: TestClient):
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": AJAX, "chain_id": 1},
        )
        assert resp.status_code == 200
        keys = set(resp.json().keys())
        assert keys == {"session_token", "wallet_address", "chain_id", "expires_at"}

    def test_connect_unsupported_chain_returns_422(self, client: TestClient):
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": AJAX, "chain_id": 999999},
        )
        assert resp.status_code == 422
        assert resp.json()["error_code"] == "UNSUPPORTED_CHAIN"

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


class TestSanctionsGuardEndpoint:
    """FEATURE 3.1.2 — sanctions screening executes before session creation."""

    def _client_with_denylist(self) -> tuple[TestClient, InMemoryRedis]:
        redis = InMemoryRedis()
        svc = WalletSessionService(redis)
        guard = SanctionsGuard(
            InMemorySanctionsScreener([SANCTIONED]), enabled=True
        )
        return _make_client(svc, guard=guard), redis

    def test_sanctioned_address_returns_403_with_error_code(self):
        client, _ = self._client_with_denylist()
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": SANCTIONED, "chain_id": 1},
        )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "sanctioned_address"

    def test_sanctioned_address_is_blocked_before_session_creation(self):
        client, redis = self._client_with_denylist()
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": SANCTIONED.upper(), "chain_id": 1},
        )
        assert resp.status_code == 403
        assert redis._store == {}

    def test_non_sanctioned_address_is_allowed(self):
        client, _ = self._client_with_denylist()
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": AJAX, "chain_id": 1},
        )
        assert resp.status_code == 200

    def test_screening_disabled_allows_denylisted_address(self):
        redis = InMemoryRedis()
        svc = WalletSessionService(redis)
        guard = SanctionsGuard(
            InMemorySanctionsScreener([SANCTIONED]), enabled=False
        )
        client = _make_client(svc, guard=guard)
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": SANCTIONED, "chain_id": 1},
        )
        assert resp.status_code == 200


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
        session_id = connect["session_token"]

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
        session_id = connect["session_token"]
        resp = client.delete(
            "/wallet/session", headers={"X-Session-Id": session_id}
        )
        body = resp.text.lower()
        assert "private_key" not in body
        assert "private" not in body