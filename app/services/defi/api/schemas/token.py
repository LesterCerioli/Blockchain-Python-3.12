from pydantic import BaseModel


class TokenResponse(BaseModel):
    address: str
    symbol: str
    name: str
    decimals: int
    chain_id: int
