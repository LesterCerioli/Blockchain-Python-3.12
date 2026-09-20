import json
import re
from collections.abc import Awaitable, Callable
from typing import Optional
from uuid import UUID, uuid4

from redis.asyncio import Redis

from ..domain.entities.wallet_session import WalletSession
from ..domain.exceptions import (
    InvalidAddressError,
    NonCustodialViolationError,
    UnsupportedChainError,
)

_SESSION_KEY_PREFIX = "defi:session:"
SESSION_TTL_SECONDS = 24 * 60 * 60

DEFAULT_SUPPORTED_CHAIN_IDS: frozenset[int] = frozenset({1, 137, 42161})

_EVM_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_HEX_ONLY_RE = re.compile(r"^[0-9a-fA-F]+$")
_PRIVATE_KEY_RE = re.compile(r"^(?:0x)?[0-9a-fA-F]{64}$")


async def _default_resolve_ens(name: str) -> str:
    raise InvalidAddressError(name)


class WalletSessionService:
    """Manages non-custodial client wallet sessions.

    Sessions are ephemeral and stored in Redis under ``defi:session:{session_id}``
    with a 24h TTL. Only the *public* ``wallet_address`` and ``chain_id`` are ever
    persisted — a private key is never accepted or stored.
    """

    def __init__(
        self,
        redis_client: Redis,
        *,
        resolve_ens: Optional[Callable[[str], Awaitable[str]]] = None,
        session_ttl_seconds: int = SESSION_TTL_SECONDS,
        supported_chain_ids: Optional[tuple[int, ...] | frozenset[int] | list[int]] = None,
    ) -> None:
        self._redis = redis_client
        self._resolve_ens = resolve_ens or _default_resolve_ens
        self._ttl = session_ttl_seconds
        self._supported_chain_ids = (
            frozenset(supported_chain_ids)
            if supported_chain_ids is not None
            else DEFAULT_SUPPORTED_CHAIN_IDS
        )

    @staticmethod
    def _key(session_id: object) -> str:
        return f"{_SESSION_KEY_PREFIX}{session_id}"

    @property
    def session_ttl_seconds(self) -> int:
        return self._ttl

    async def connect(self, wallet_address: str, chain_id: int) -> WalletSession:
        if chain_id not in self._supported_chain_ids:
            raise UnsupportedChainError(chain_id, tuple(self._supported_chain_ids))
        address = await self._resolve_address(wallet_address)
        address = self._normalize_and_validate(address)
        session = WalletSession(
            wallet_address=address,
            session_id=str(uuid4()),
            chain_id=chain_id,
        )
        payload = json.dumps(
            {
                "wallet_address": session.wallet_address,
                "chain_id": session.chain_id,
            },
            separators=(",", ":"),
        )
        await self._redis.setex(self._key(session.session_id), self._ttl, payload)
        return session

    async def disconnect(self, session_id: UUID) -> None:
        await self._redis.delete(self._key(session_id))

    async def get_session(self, session_id: UUID) -> Optional[WalletSession]:
        raw = await self._redis.get(self._key(session_id))
        if raw is None:
            return None
        data = json.loads(raw)
        return WalletSession(
            wallet_address=data["wallet_address"],
            session_id=str(session_id),
            chain_id=int(data["chain_id"]),
        )

    async def _resolve_address(self, raw: str) -> str:
        candidate = raw.strip()
        if candidate.lower().endswith(".eth"):
            resolved = await self._resolve_ens(candidate)
            if not resolved:
                raise InvalidAddressError(candidate)
            return resolved
        return candidate

    @staticmethod
    def _normalize_and_validate(value: str) -> str:
        candidate = value.strip().lower()
        if _PRIVATE_KEY_RE.fullmatch(candidate):
            raise NonCustodialViolationError(
                "PRIVATE_KEY_EXPOSURE",
                "A private key must never be sent to the platform",
            )
        if not (
            (candidate.startswith("0x") and len(candidate) == 42)
            and _HEX_ONLY_RE.fullmatch(candidate[2:]) is not None
        ):
            raise InvalidAddressError(value)
        return candidate