from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from web3 import Web3

from ..exceptions import InvalidAddressError

_ENS_SUFFIX = ".eth"


@dataclass(frozen=True)
class TokenAddress:
    value: str
    web3_instance: Any = field(default=None, compare=False, hash=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            self._normalize(self.value, self.web3_instance),
        )

    @staticmethod
    def _normalize(raw: Any, web3_instance: Any = None) -> str:
        if not isinstance(raw, str) or not raw.strip():
            raise InvalidAddressError(str(raw))
        candidate = raw.strip()
        if candidate.lower().endswith(_ENS_SUFFIX):
            candidate = TokenAddress._resolve_ens(candidate, web3_instance)
        return TokenAddress._to_checksum(candidate)

    @staticmethod
    def _resolve_ens(name: str, web3_instance: Any) -> str:
        if web3_instance is None or getattr(web3_instance, "ens", None) is None:
            raise InvalidAddressError(name)
        try:
            resolved = web3_instance.ens.address(name)
        except Exception as exc:
            raise InvalidAddressError(name) from exc
        if not resolved:
            raise InvalidAddressError(name)
        return str(resolved)

    @staticmethod
    def _to_checksum(address: str) -> str:
        if not isinstance(address, str) or not address.startswith("0x"):
            raise InvalidAddressError(str(address))
        body = address[2:]
        if len(body) != 40:
            raise InvalidAddressError(address)
        try:
            int(body, 16)
        except ValueError as exc:
            raise InvalidAddressError(address) from exc
        has_letters = any(char.isalpha() for char in body)
        uniform_case = body.islower() or body.isupper()
        if has_letters and not uniform_case and not Web3.is_checksum_address(address):
            raise InvalidAddressError(address)
        try:
            return Web3.to_checksum_address(address)
        except (ValueError, TypeError) as exc:
            raise InvalidAddressError(address) from exc

    @classmethod
    async def from_ens(cls, name: str, web3_instance: Any) -> "TokenAddress":
        if not isinstance(name, str) or not name.strip():
            raise InvalidAddressError(str(name))
        candidate = name.strip()
        if not candidate.lower().endswith(_ENS_SUFFIX):
            raise InvalidAddressError(candidate)
        if web3_instance is None or getattr(web3_instance, "ens", None) is None:
            raise InvalidAddressError(candidate)
        try:
            resolved = await web3_instance.ens.address(candidate)
        except Exception as exc:
            raise InvalidAddressError(candidate) from exc
        if not resolved:
            raise InvalidAddressError(candidate)
        return cls(str(resolved))

    def __str__(self) -> str:
        return self.value
