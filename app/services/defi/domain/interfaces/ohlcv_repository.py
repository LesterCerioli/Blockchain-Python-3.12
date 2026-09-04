from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..value_objects.ohlcv import OHLCVCandle


class IOHLCVRepository(ABC):
    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        interval: str,
        from_ts: datetime,
        to_ts: datetime,
    ) -> list["OHLCVCandle"]: ...
