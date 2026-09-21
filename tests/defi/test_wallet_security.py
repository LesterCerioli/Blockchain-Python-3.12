"""Security tests for FEATURE 3.1.2 — POST /defi/wallet/connect.

Covers the three security surfaces of non-custodial wallet connection:

1. Non-custodial invariant — no key material is ever accepted, stored or echoed.
2. Sanctions screening — a sanctioned address is blocked *before* session creation.
3. Input hardening — malformed / oversized / injected addresses never persist.

Mirrors the repository convention established by
``tests/tokenization/test_choice_security.py``.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.auth.api.dependencies import get_current_token
from app.services.defi.api.exception_handlers import (
    register_defi_exception_handlers,
)
from app.services.defi.api.middleware.sanctions_guard import SanctionsGuard
from app.services.defi.api.routers.wallet_router import wallet_router
from app.services.defi.api.schemas.wallet import (
    WalletConnectRequest,
    WalletConnectResponse,
)
from app.services.defi.application.wallet_session_service import (
    WalletSessionService,
)
from app.services.defi.domain.entities.wallet_session import WalletSession
from app.services.defi.domain.exceptions import (
    InvalidAddressError,
    NonCustodialViolationError,
)
from app.services.defi.infrastructure.compliance.in_memory_sanctions_screener import (
    InMemorySanctionsScreener,
)

AJAX = "0x" + "a" * 40
SANCTIONED = "0x" + "d" * 40
PRIVATE_KEY = "0x" + "b" * 64

FORBIDDEN_KEY_TERMS = ("private_key", "privatekey", "seed_phrase", "mnemonic", "secret")


def _run(coro):
    """Run an awaitable synchronously (tests are plain, not async)."""
    return asyncio.run(coro)


class InMemoryRedis:
    
    def __init__(self) -> None:
        self.store: dict[str, tuple[str, int]] = {}

    async def setex(self, key: str, seconds: int, value: str) -> None:
        self.store[key] = (value, seconds)

    async def get(self, key: str) -> str | None:
        entry = self.store.get(key)
        return entry[0] if entry else None

    async def delete(self, key: str) -> int:
        return 1 if self.store.pop(key, None) is not None else 0


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


def _client_with_denylist() -> tuple[TestClient, InMemoryRedis]:
    redis = InMemoryRedis()
    guard = SanctionsGuard(InMemorySanctionsScreener([SANCTIONED]), enabled=True)
    return _make_client(WalletSessionService(redis), guard=guard), redis


# ---------------------------------------------------------------------------
# 1. Non-custodial invariant — key material is never accepted or persisted
# ---------------------------------------------------------------------------


class TestNonCustodialInvariant:

    def test_private_key_shaped_address_is_rejected_and_not_persisted(self):
        redis = InMemoryRedis()
        client = _make_client(WalletSessionService(redis))
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": PRIVATE_KEY, "chain_id": 1},
        )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "NON_CUSTODIAL_VIOLATION"
        assert redis.store == {}

    def test_bare_64_hex_private_key_is_rejected(self):
        client = _make_client(WalletSessionService(InMemoryRedis()))
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": "a" * 64, "chain_id": 1},
        )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "NON_CUSTODIAL_VIOLATION"

    def test_redis_payload_contains_only_public_address_and_chain(self):
        redis = InMemoryRedis()
        svc = WalletSessionService(redis)
        session = _run(svc.connect(AJAX, 1))
        raw = _run(redis.get(f"defi:session:{session.session_id}"))
        assert json.loads(raw) == {"wallet_address": AJAX, "chain_id": 1}

    def test_redis_payload_never_contains_key_material_terms(self):
        redis = InMemoryRedis()
        svc = WalletSessionService(redis)
        session = _run(svc.connect(AJAX, 1))
        raw = _run(redis.get(f"defi:session:{session.session_id}")).lower()
        for term in FORBIDDEN_KEY_TERMS:
            assert term not in raw

    def test_connect_response_has_no_key_material(self):
        client = _make_client(WalletSessionService(InMemoryRedis()))
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": AJAX, "chain_id": 1},
        )
        assert resp.status_code == 200
        assert set(resp.json().keys()) == {
            "session_token",
            "wallet_address",
            "chain_id",
            "expires_at",
        }
        body = resp.text.lower()
        for term in FORBIDDEN_KEY_TERMS:
            assert term not in body

    def test_response_schema_exposes_only_public_fields(self):
        for model in (WalletConnectResponse, WalletConnectRequest):
            for field_name in model.model_fields:
                for term in FORBIDDEN_KEY_TERMS:
                    assert term not in field_name.lower()

    def test_wallet_session_entity_rejects_private_key(self):
        with pytest.raises(ValueError):
            WalletSession(
                wallet_address=PRIVATE_KEY,
                session_id="sid",
                chain_id=1,
            )

    def test_ens_resolved_private_key_shape_is_rejected(self):
        redis = InMemoryRedis()

        async def malicious_resolver(name: str) -> str:
            return PRIVATE_KEY

        svc = WalletSessionService(redis, resolve_ens=malicious_resolver)
        with pytest.raises(NonCustodialViolationError):
            _run(svc.connect("attacker.eth", 1))
        assert redis.store == {}


# ---------------------------------------------------------------------------
# 2. Sanctions screening — blocked before session creation
# ---------------------------------------------------------------------------


class TestSanctionsScreening:

    def test_sanctioned_address_returns_403_sanctioned_address(self):
        client, _ = _client_with_denylist()
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": SANCTIONED, "chain_id": 1},
        )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "sanctioned_address"

    def test_sanctioned_address_blocked_before_any_session_is_created(self):
        client, redis = _client_with_denylist()
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": SANCTIONED, "chain_id": 1},
        )
        assert resp.status_code == 403
        assert redis.store == {}

    def test_case_obfuscation_bypass_attempt_is_blocked(self):
        client, _ = _client_with_denylist()
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": "0X" + "D" * 40, "chain_id": 1},
        )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "sanctioned_address"

    def test_whitespace_obfuscation_bypass_attempt_is_blocked(self):
        client, _ = _client_with_denylist()
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": f"  {SANCTIONED.upper()}  ", "chain_id": 1},
        )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "sanctioned_address"

    def test_non_sanctioned_address_is_not_blocked(self):
        client, _ = _client_with_denylist()
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": AJAX, "chain_id": 1},
        )
        assert resp.status_code == 200

    def test_disabled_screening_does_not_bypass_non_custodial_check(self):
        redis = InMemoryRedis()
        guard = SanctionsGuard(
            InMemorySanctionsScreener([SANCTIONED]), enabled=False
        )
        client = _make_client(WalletSessionService(redis), guard=guard)
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": PRIVATE_KEY, "chain_id": 1},
        )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "NON_CUSTODIAL_VIOLATION"
        assert redis.store == {}


# ---------------------------------------------------------------------------
# 3. Input hardening — malformed input never persists
# ---------------------------------------------------------------------------


class TestInputHardening:

    @pytest.mark.parametrize(
        "evil_address",
        [
            "'; DROP TABLE defi_sessions; --",
            "0x" + "a" * 39,  # too short
            "0x" + "a" * 41,  # too long
            "0x" + "g" * 40,  # non-hex
            "<script>alert(1)</script>",
            "../../etc/passwd",
            "not-an-address",
        ],
    )
    def test_malformed_address_is_rejected_and_not_persisted(self, evil_address: str):
        redis = InMemoryRedis()
        client = _make_client(WalletSessionService(redis))
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": evil_address, "chain_id": 1},
        )
        assert resp.status_code in (400, 422)
        assert redis.store == {}

    def test_service_rejects_oversized_hex(self):
        svc = WalletSessionService(InMemoryRedis())
        with pytest.raises(InvalidAddressError):
            _run(svc.connect("0x" + "a" * 4000, 1))

    def test_unsupported_chain_is_rejected_before_persistence(self):
        redis = InMemoryRedis()
        client = _make_client(WalletSessionService(redis))
        resp = client.post(
            "/wallet/connect",
            json={"wallet_address": AJAX, "chain_id": 999999},
        )
        assert resp.status_code == 422
        assert resp.json()["error_code"] == "UNSUPPORTED_CHAIN"
        assert redis.store == {}
