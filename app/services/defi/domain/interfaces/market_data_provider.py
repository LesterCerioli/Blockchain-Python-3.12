from abc import ABC, abstractmethod

from ..value_objects.market_quote import MarketQuote
from ..value_objects.ohlcv_candle import OHLCVCandle


class IMarketDataProvider(ABC):

    @abstractmethod
    async def get_quote(self, symbol: str, vs_currency: str = "usd") -> MarketQuote: ...

    @abstractmethod
    async def get_quotes(
        self, symbols: list[str], vs_currency: str = "usd"
    ) -> list[MarketQuote]: ...

    @abstractmethod
    async def get_ohlcv(
        self, symbol: str, vs_currency: str = "usd", days: int = 1
    ) -> list[OHLCVCandle]: ...
