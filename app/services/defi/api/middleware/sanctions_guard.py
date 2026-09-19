import json

from fastapi import Request

from ...domain.exceptions import SanctionedAddressError
from ...domain.interfaces.sanctions_screener import ISanctionsScreener


class SanctionsGuard:
    
    def __init__(self, screener: ISanctionsScreener, enabled: bool = True) -> None:
        self._screener = screener
        self._enabled = enabled

    async def __call__(self, request: Request) -> None:
        if not self._enabled:
            return

        address = await self._extract_wallet_address(request)
        if address and await self._screener.is_sanctioned(address):
            raise SanctionedAddressError(address)

    @staticmethod
    async def _extract_wallet_address(request: Request) -> str | None:
        try:
            body = await request.json()
        except (json.JSONDecodeError, ValueError):
            return None
        if not isinstance(body, dict):
            return None
        wallet_address = body.get("wallet_address")
        if not isinstance(wallet_address, str) or not wallet_address.strip():
            return None
        return wallet_address.strip()
