from pydantic import BaseModel, Field


class ChainConfigResponse(BaseModel):
    chain_id: int = Field(description="EVM chain identifier")
    name: str = Field(description="Human-readable chain name")
    explorer: str = Field(description="Block explorer base URL")
    is_testnet: bool = Field(description="Whether this chain is a test network")

    model_config = {"populate_by_name": True}
