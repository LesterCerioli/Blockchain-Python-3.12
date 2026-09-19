from abc import ABC, abstractmethod


class ISanctionsScreener(ABC):
    """Port for sanctions / OFAC screening of public wallet addresses.

    Implementations only ever receive a *public* address — never key material.
    """

    @abstractmethod
    async def is_sanctioned(self, address: str) -> bool:
        """Returns True when the public address matches a sanctions list."""
        ...
