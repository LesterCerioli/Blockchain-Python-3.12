from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime


@dataclass(frozen=True)
class OHLCVCandle:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
