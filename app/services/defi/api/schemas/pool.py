from pydantic import BaseModel

from .token import TokenResponse


class PoolResponse(BaseModel):
    address: str
    token0: TokenResponse
    token1: TokenResponse
    fee_bps: int
    protocol: str
    chain_id: int
    liquidity: int
