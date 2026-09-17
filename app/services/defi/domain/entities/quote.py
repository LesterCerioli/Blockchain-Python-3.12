from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class Quote(BaseModel):
    token_in: str
    token_out: str
    amount_in: Decimal = Field(gt=0)
    amount_out: Decimal = Field(gt=0)
    price_impact_bps: int = Field(ge=0)
    slippage_bps: int = Field(ge=0, le=10_000)
    chain_id: int = Field(gt=0)

    @field_validator("token_in", "token_out")
    @classmethod
    def normalize_address(cls, v: str) -> str:
        return v.lower()

    model_config = {"frozen": True}
