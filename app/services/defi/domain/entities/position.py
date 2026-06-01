import uuid
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from .pool import Pool


class Position(BaseModel):
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    pool: Pool
    owner: str
    liquidity: int = Field(ge=0)
    amount0: Decimal = Field(ge=0, default=Decimal(0))
    amount1: Decimal = Field(ge=0, default=Decimal(0))

    @field_validator("owner")
    @classmethod
    def normalize_owner(cls, v: str) -> str:
        return v.lower()

    model_config = {"frozen": True}
