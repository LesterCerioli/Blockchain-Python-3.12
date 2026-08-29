from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class MarketQuote:
    symbol: str
    vs_currency: str
    price: Decimal
    price_change_24h: Optional[Decimal]
    timestamp: datetime

    def __post_init__(self) -> None:
        if self.price < 0:
            raise ValueError("MarketQuote.price must be >= 0")
