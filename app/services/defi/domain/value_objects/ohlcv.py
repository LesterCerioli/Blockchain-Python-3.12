from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class OHLCVCandle:
    symbol: str
    open_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    def __post_init__(self) -> None:
        if self.open_time.tzinfo is None:
            raise ValueError("OHLCVCandle.open_time must be timezone-aware")
        if self.high < self.open or self.low > self.open:
            raise ValueError("high >= open and low <= open required")
        if self.close < self.low or self.close > self.high:
            raise ValueError("close must be within low and high")
