from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WalletConnectRequest(BaseModel):
    wallet_address: str = Field(
        min_length=1,
        description="Public EVM address (0x...) or ENS name. A private key is never accepted.",
    )
    chain_id: int = Field(gt=0, description="EVM chain id targeted by this session")


class WalletConnectResponse(BaseModel):
    
    session_token: str = Field(description="Opaque session token (UUID v4)")
    wallet_address: str = Field(description="Public EVM address bound to the session")
    chain_id: int = Field(gt=0, description="EVM chain id bound to the session")
    expires_at: datetime = Field(description="UTC timestamp when the session expires")

    model_config = ConfigDict(frozen=True)


class WalletDisconnectResponse(BaseModel):
    detail: str = "session revoked"

    model_config = ConfigDict(frozen=True)