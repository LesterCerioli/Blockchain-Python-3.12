from pydantic import BaseModel, Field, field_validator


class WalletSession(BaseModel):
    wallet_address: str
    session_id: str
    chain_id: int = Field(gt=0)

    @field_validator("wallet_address")
    @classmethod
    def reject_private_key_format(cls, v: str) -> str:
        candidate = v.lower().removeprefix("0x")
        if len(candidate) == 64 and all(c in "0123456789abcdef" for c in candidate):
            raise ValueError("wallet_address must not be a private key (64 hex chars)")
        return v.lower()

    model_config = {"frozen": True}
