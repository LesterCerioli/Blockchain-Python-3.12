from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from ..entities.market_index import MarketIndex
from ..value_objects.price import Price
from ..value_objects.price_point import PricePoint


class IMarketDataProvider(ABC):

    @abstractmethod
    async def get_token_price(self, token_address: str, chain_id: int) -> Optional[Price]: ...

    @abstractmethod
    async def get_price_change_24h(self, token_address: str, chain_id: int) -> Optional[Decimal]:
        """Returns price change percentage over the last 24 h (e.g. -3.5 means -3.5%)."""
        ...

    @abstractmethod
    async def get_token_volume_24h(self, token_address: str, chain_id: int) -> Optional[Decimal]:
        """Returns trading volume in USD over the last 24 h."""
        ...

    @abstractmethod
    async def get_market_cap(self, token_address: str, chain_id: int) -> Optional[Decimal]:
        """Returns market capitalisation in USD."""
        ...

    @abstractmethod
    async def get_historical_prices(
        self,
        token_address: str,
        chain_id: int,
        from_timestamp: int,
        to_timestamp: int,
    ) -> list[PricePoint]:
        """Returns OHLCV-style price snapshots between two Unix timestamps (inclusive)."""
        ...

    @abstractmethod
    async def get_market_index(self, symbol: str) -> Optional[MarketIndex]: ...

    @abstractmethod
    async def list_market_indices(self) -> list[MarketIndex]: ...