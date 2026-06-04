from pydantic import BaseModel, Field, field_validator


class ChainInfo(BaseModel):
    chain_id: int = Field(gt=0)
    name: str
    native_token_symbol: str
    block_time_seconds: int = Field(gt=0)
    explorer_url: str
    is_testnet: bool = False

    @field_validator("name", "native_token_symbol", "explorer_url")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must not be blank")
        return v

    model_config = {"frozen": True}
