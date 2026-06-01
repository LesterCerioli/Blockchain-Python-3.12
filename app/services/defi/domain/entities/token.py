from pydantic import BaseModel, Field, field_validator


class Token(BaseModel):
    
    address: str
    symbol: str
    name: str
    decimals: int = Field(ge=0, le=18)
    chain_id: int = Field(gt=0)

    @field_validator("address")
    @classmethod
    def normalize_address(cls, v: str) -> str:
        return v.lower()

    @field_validator("symbol")
    @classmethod
    def symbol_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("symbol must not be blank")
        return v.upper()

    model_config = {"frozen": True}
