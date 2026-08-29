from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AssetQuote(BaseModel):
    symbol: str
    price_usd: Decimal = Field(ge=0)
    change_24h: Optional[Decimal] = None
    volume_24h: Decimal = Field(ge=0)
    market_cap: Decimal = Field(ge=0)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @field_validator("symbol")
    @classmethod
    def symbol_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("symbol must not be blank")
        return v.upper()

    model_config = {"frozen": True}
