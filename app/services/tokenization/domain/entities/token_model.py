from pydantic import BaseModel, Field


class TokenModel(BaseModel):
    standard: str
    name: str
    symbol: str
    decimals: int = Field(ge=0, le=18, default=18)
    initial_supply: int = Field(ge=0, default=0)
    max_supply: int | None = Field(default=None, ge=0)
    mintable: bool = False
    burnable: bool = False
    pausable: bool = False
    transferable: bool = True
    metadata_uri: str | None = None

    model_config = {"frozen": True}

    @property
    def has_supply_cap(self) -> bool:
        return self.max_supply is not None and self.max_supply > 0
