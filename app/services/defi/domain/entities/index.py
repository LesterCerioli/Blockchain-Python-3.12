from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel


class MarketIndex(BaseModel):
    code: str
    name: str
    description: str
    category: str

    model_config = {"frozen": True}


class TokenRanking(BaseModel):
    rank: int
    symbol: str
    name: str
    chain_id: int
    metric: str
    metric_value: str
    price_usd: str

    model_config = {"frozen": True}


class ProtocolRanking(BaseModel):
    rank: int
    protocol: str
    chain_id: int
    metric: str
    value: Decimal

    model_config = {"frozen": True}


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
