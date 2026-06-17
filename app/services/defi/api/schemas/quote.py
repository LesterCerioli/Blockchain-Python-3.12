from datetime import datetime

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


class MarketQuoteResponse(BaseModel):
    symbol: str
    price_usd: str
    change_24h_pct: float
    volume_24h_usd: str
    market_cap_usd: str
    fetched_at: datetime
