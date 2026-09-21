
from __future__ import annotations

import pytest

from app.services.defi.domain.exceptions import InvalidAddressError
from app.services.defi.domain.value_objects.token_address import TokenAddress

VITALIK_ENS = "vitalik.eth"
VITALIK_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
VITALIK_LOWER = VITALIK_ADDRESS.lower()


def _run(coro):
    """Run an awaitable synchronously (plain pytest tests)."""
    import asyncio

    return asyncio.run(coro)


class InMemoryENS:
    """In-memory ENS registry mimicking ``web3.ENS.address(name)``."""

    def __init__(self, entries: dict[str, str]) -> None:
        self._entries = {name.lower(): address for name, address in entries.items()}

    def address(self, name: str) -> str | None:
        return self._entries.get(name.lower())


class InMemoryENSAsync:
    """Async twin used to exercise the ``TokenAddress.from_ens`` await path."""

    def __init__(self, entries: dict[str, str]) -> None:
        self._entries = {name.lower(): address for name, address in entries.items()}

    async def address(self, name: str) -> str | None:
        return self._entries.get(name.lower())


class InMemoryWeb3:
    def __init__(self, ens: InMemoryENS | InMemoryENSAsync) -> None:
        self.ens = ens


@pytest.mark.integration
class TestTokenAddressENSIntegration:
    def test_vitalik_eth_resolves_to_correct_address(self) -> None:
        w3 = InMemoryWeb3(InMemoryENS({VITALIK_ENS: VITALIK_LOWER}))
        token = TokenAddress(VITALIK_ENS, web3_instance=w3)

        assert token.value == VITALIK_ADDRESS

    def test_ens_lowercase_result_is_normalized_to_checksum(self) -> None:
        w3 = InMemoryWeb3(InMemoryENS({VITALIK_ENS: VITALIK_LOWER}))
        token = TokenAddress(VITALIK_ENS, web3_instance=w3)

        assert token.value == VITALIK_ADDRESS
        assert str(token) == VITALIK_ADDRESS

    def test_unknown_ens_name_raises_invalid_address(self) -> None:
        w3 = InMemoryWeb3(InMemoryENS({VITALIK_ENS: VITALIK_LOWER}))

        with pytest.raises(InvalidAddressError):
            TokenAddress("unknown.eth", web3_instance=w3)

    def test_missing_web3_instance_raises_invalid_address(self) -> None:
        with pytest.raises(InvalidAddressError):
            TokenAddress(VITALIK_ENS)

    def test_from_ens_async_resolves_vitalik_eth(self) -> None:
        w3 = InMemoryWeb3(InMemoryENSAsync({VITALIK_ENS: VITALIK_ADDRESS}))
        token = _run(TokenAddress.from_ens(VITALIK_ENS, web3_instance=w3))

        assert token.value == VITALIK_ADDRESS