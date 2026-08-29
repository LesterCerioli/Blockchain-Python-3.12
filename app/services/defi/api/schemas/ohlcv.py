from datetime import datetime

from pydantic import BaseModel


class OHLCVCandle(BaseModel):
    open_time: datetime
    open: str
    high: str
    low: str
    close: str
    volume: str


class OHLCVResponse(BaseModel):
    symbol: str
    interval: str
    candles: list[OHLCVCandle]
