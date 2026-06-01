from pydantic import BaseModel, Field, field_validator

from .token import Token


class Pool(BaseModel):
    
    address: str
    token0: Token
    token1: Token
    fee_bps: int = Field(ge=0, description="Fee in basis points (e.g. 30 = 0.3%)")
    protocol: str
    chain_id: int = Field(gt=0)
    liquidity: int = Field(ge=0, default=0)

    @field_validator("address")
    @classmethod
    def normalize_address(cls, v: str) -> str:
        return v.lower()

    @field_validator("protocol")
    @classmethod
    def protocol_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("protocol must not be blank")
        return v

    model_config = {"frozen": True}
