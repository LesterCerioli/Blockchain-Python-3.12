from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator

_SIGNING_FIELDS = {"v", "r", "s"}


class UnsignedTransaction(BaseModel):
    to: str
    from_address: str
    value: Decimal = Field(ge=0)
    data: str = "0x"
    gas: int = Field(gt=0)
    gas_price: Decimal = Field(ge=0)
    nonce: int = Field(ge=0)
    chain_id: int = Field(gt=0)

    @model_validator(mode="before")
    @classmethod
    def reject_signing_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            present = _SIGNING_FIELDS & values.keys()
            if present:
                raise ValueError(
                    f"Signing fields must not be present on UnsignedTransaction: {sorted(present)}"
                )
        return values

    model_config = {"frozen": True}
