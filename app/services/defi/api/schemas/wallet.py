from pydantic import BaseModel, ConfigDict, Field


class WalletConnectRequest(BaseModel):
    wallet_address: str = Field(
        min_length=1,
        description="Public EVM address (0x...) or ENS name. A private key is never accepted.",
    )
    chain_id: int = Field(gt=0, description="EVM chain id targeted by this session")


class WalletDisconnectResponse(BaseModel):
    detail: str = "session revoked"

    model_config = ConfigDict(frozen=True)