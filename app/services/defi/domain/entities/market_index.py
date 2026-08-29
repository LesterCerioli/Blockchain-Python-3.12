from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class MarketIndex(BaseModel):
    symbol: str
    name: str
    value: Decimal = Field(ge=0)
    timestamp: datetime

    @field_validator("symbol")
    @classmethod
    def symbol_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("symbol must not be blank")
        return v.upper()

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v

    model_config = {"frozen": True}
