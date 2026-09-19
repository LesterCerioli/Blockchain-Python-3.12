from collections.abc import Iterable

from ...domain.interfaces.sanctions_screener import ISanctionsScreener


class InMemorySanctionsScreener(ISanctionsScreener):
    """Local sanctions screener backed by a static deny-list of public addresses.

    Addresses are normalised to lowercase so a checksummed input and its
    lowercase form are screened identically. Intended for local/dev and tests;
    production may replace it with an OFAC-provider adapter behind the same
    ``ISanctionsScreener`` port without touching the application layer.
    """

    def __init__(self, sanctioned_addresses: Iterable[str] = ()) -> None:
        self._sanctioned = {
            address.strip().lower()
            for address in sanctioned_addresses
            if isinstance(address, str) and address.strip()
        }

    async def is_sanctioned(self, address: str) -> bool:
        if not isinstance(address, str):
            return False
        return address.strip().lower() in self._sanctioned
