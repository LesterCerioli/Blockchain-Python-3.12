from __future__ import annotations

import json
from typing import Optional

import pytest
from redis.asyncio import Redis

from app.services.defi.application.wallet_session_service import (
    WalletSessionService,
)
from app.services.defi.domain.entities.wallet_session import WalletSession
from app.services.defi.domain.exceptions import (
    InvalidAddressError,
    NonCustodialViolationError,
)

VAL = "0x" + "A" * 2 + "a" * 38
LOWER = "0x" + "a" * 40


class InMemoryRedis:
    """Minimal async Redis double (setex/get/get/setex/delete/ttl/keys)."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, Optional[int]]] = {}

    async def setex(self, key: str, seconds: int, value: str) -> None:
        self._store[key] = (value, seconds)

    async def get(self, key: str) -> Optional[str]:
        entry = self._store.get(key)
        return entry[0] if entry else None

    async def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0

    async def ttl(self, key: str) -> int:
        entry = self._store.get(key)
        return entry[1] if entry else -2

    async def keys(self, pattern: str) -> list[str]:
        prefix = pattern[:-1]
        return [k for k in self._store if k.startswith(prefix)]


async def _fake_resolve_ens(name: str) -> str:
    return LOWER


def _svc(resolve_ens=None, redis: Redis | None = None) -> WalletSessionService:
    return WalletSessionService(
        redis or InMemoryRedis(),  # type: ignore[arg-type]
        resolve_ens=resolve_ens,
    )


# ---------------------------------------------------------------------------
# connect — valid public address
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestConnectValidAddress:

    async def test_returns_wallet_session_with_uuid4(self):
        session = await _svc().connect(VAL, 1)
        assert isinstance(session, WalletSession)
        assert session.wallet_address == LOWER
        assert session.chain_id == 1
        assert len(session.session_id) == 36
        assert "-" in session.session_id

    async def test_address_normalized_lowercase(self):
        session = await _svc().connect("0xABCDEF1234567890ABCDEF1234567890ABCDEF12", 1)
        assert session.wallet_address == "0xabcdef1234567890abcdef1234567890abcdef12"

    async def test_stored_in_redis_at_defi_session_key(self):
        redis = InMemoryRedis()
        session = await _svc(redis=redis).connect(VAL, 137)
        stored = await redis.get(f"defi:session:{session.session_id}")
        assert stored is not None

    async def test_redis_payload_contains_only_public_address_and_chain_id(self):
        redis = InMemoryRedis()
        session = await _svc(redis=redis).connect(VAL, 42161)
        stored = await redis.get(f"defi:session:{session.session_id}")
        data = json.loads(stored)
        assert data == {"wallet_address": LOWER, "chain_id": 42161}

    async def test_redis_payload_never_contains_private_key_material(self):
        redis = InMemoryRedis()
        session = await _svc(redis=redis).connect(VAL, 1)
        stored = await redis.get(f"defi:session:{session.session_id}")
        body = str(stored).lower()
        for forbidden in ("private_key", "privatekey", " seed", "mnemonic"):
            assert forbidden not in body

    async def test_redis_key_has_24h_ttl(self):
        redis = InMemoryRedis()
        session = await _svc(redis=redis).connect(VAL, 1)
        ttl = await redis.ttl(f"defi:session:{session.session_id}")
        assert 0 < ttl <= 24 * 60 * 60


# ---------------------------------------------------------------------------
# connect — invalid / private-key-shaped input (DoD + non-custodial invariant)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestConnectInvalidAddress:

    async def test_non_address_raises_invalid_address_error(self):
        with pytest.raises(InvalidAddressError):
            await _svc().connect("not-a-valid-address", 1)

    async def test_empty_string_raises_invalid_address_error(self):
        with pytest.raises(InvalidAddressError):
            await _svc().connect("", 1)

    async def test_too_short_hex_raises_invalid_address_error(self):
        with pytest.raises(InvalidAddressError):
            await _svc().connect("0x1234", 1)

    async def test_64_hex_without_prefix_raises_non_custodial_violation(self):
        with pytest.raises(NonCustodialViolationError):
            await _svc().connect("a" * 64, 1)

    async def test_0x_plus_64_hex_raises_non_custodial_violation(self):
        with pytest.raises(NonCustodialViolationError):
            await _svc().connect("0x" + "b" * 64, 1)

    async def test_nothing_is_persisted_on_failure(self):
        redis = InMemoryRedis()
        svc = _svc(redis=redis)
        with pytest.raises(InvalidAddressError):
            await svc.connect("bad", 1)
        with pytest.raises(NonCustodialViolationError):
            await svc.connect("a" * 64, 1)
        assert await redis.keys("defi:session:*") == []


# ---------------------------------------------------------------------------
# connect — ENS resolution
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestENSResolution:

    async def test_ens_name_resolves_to_evm_address(self):
        session = await _svc(resolve_ens=_fake_resolve_ens).connect("alice.eth", 1)
        assert session.wallet_address == LOWER

    async def test_ens_name_without_resolver_raises_invalid_address(self):
        with pytest.raises(InvalidAddressError):
            await _svc().connect("alice.eth", 1)

    async def test_resolved_value_invalid_raises_invalid_address(self):
        async def bad_resolve(name: str) -> str:
            return "not-a-valid-address"

        with pytest.raises(InvalidAddressError):
            await _svc(resolve_ens=bad_resolve).connect("alice.eth", 1)

    async def test_ens_resolver_result_is_never_stored_as_private_key(self):
        redis = InMemoryRedis()

        async def resolve(name: str) -> str:
            return "0x" + "c" * 64  # private-key-shaped -> must be rejected

        svc = _svc(resolve_ens=resolve, redis=redis)
        with pytest.raises(NonCustodialViolationError):
            await svc.connect("bob.eth", 1)
        assert await redis.keys("defi:session:*") == []


# ---------------------------------------------------------------------------
# get_session
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestGetSession:

    async def test_returns_session_when_exists(self):
        svc = _svc()
        session = await svc.connect(VAL, 1)
        result = await svc.get_session(session.session_id)
        assert result is not None
        assert result.wallet_address == LOWER
        assert result.chain_id == 1
        assert result.session_id == session.session_id

    async def test_expired_or_missing_returns_none(self):
        svc = _svc()
        result = await svc.get_session("00000000-0000-0000-0000-000000000000")
        assert result is None


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDisconnect:

    async def test_disconnect_revokes_session(self):
        svc = _svc()
        session = await svc.connect(VAL, 1)
        await svc.disconnect(session.session_id)
        assert await svc.get_session(session.session_id) is None

    async def test_disconnect_nonexistent_session_no_error(self):
        svc = _svc()
        await svc.disconnect("00000000-0000-0000-0000-000000000000")  # must not raise

    async def test_disconnect_removes_redis_key(self):
        redis = InMemoryRedis()
        svc = _svc(redis=redis)
        session = await svc.connect(VAL, 1)
        await svc.disconnect(session.session_id)
        assert await redis.get(f"defi:session:{session.session_id}") is None