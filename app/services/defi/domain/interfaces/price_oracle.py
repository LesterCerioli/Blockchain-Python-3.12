from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from ..value_objects.price import Price


class IPriceOracle(ABC):

    @abstractmethod
    async def get_price(
        self,
        base_token_address: str,
        quote_token_address: str,
        chain_id: int,
    ) -> Optional[Price]: ...

    @abstractmethod
    async def get_price_usd(self, token_address: str, chain_id: int) -> Optional[Price]: ...

    @abstractmethod
    async def get_twap(
        self,
        base_token_address: str,
        quote_token_address: str,
        period_seconds: int,
        chain_id: int,
    ) -> Optional[Price]:
        """Returns the time-weighted average price over the given period."""
        ...

    @abstractmethod
    async def get_price_with_confidence(
        self,
        base_token_address: str,
        quote_token_address: str,
        chain_id: int,
    ) -> tuple[Optional[Price], Decimal]:
        """Returns (price, confidence) where confidence is in [0, 1]; 1.0 = fully confident."""
        ...

    @abstractmethod
    async def is_price_stale(
        self,
        base_token_address: str,
        quote_token_address: str,
        chain_id: int,
        max_age_seconds: int,
    ) -> bool:
        """Returns True when the last price update is older than max_age_seconds."""
        ...
