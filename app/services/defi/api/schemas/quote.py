from pydantic import BaseModel, Field


class QuoteRequest(BaseModel):
    token_in: str
    token_out: str
    amount_in_raw: int = Field(gt=0)
    chain_id: int = Field(gt=0)
    slippage_bps: int = Field(default=50, ge=0, le=10_000)


class QuoteResponse(BaseModel):
    token_in: str
    token_out: str
    amount_in: str
    amount_out: str
    price_impact_bps: int
    slippage_bps: int
    pool_count: int
