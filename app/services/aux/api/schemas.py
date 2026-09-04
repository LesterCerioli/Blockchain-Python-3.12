from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


# -- request bodies -------------------------------------------------------
class SessionCreate(BaseModel):
    email: str
    ip_address: str
    user_agent: str
    max_duration_ms: int | None = None


class KycCreate(BaseModel):
    email: str
    full_name: str
    verification_level: str
    identity_document: str
    document_path: str
    attached_documents: list[str] | None = None


class MetadataCreate(BaseModel):
    email: str
    metadata_key: str
    metadata_value: str


class AuditCreate(BaseModel):
    email: str
    action: str
    resource: str
    details: str


class TokenMetaUpsert(BaseModel):
    symbol: str
    volume_24h: Decimal
    max_price_24h: Decimal
    min_price_24h: Decimal
    current_price: Decimal
    last_check: str


class OhlcvCreate(BaseModel):
    symbol: str
    interval: str
    open_time: int
    open_price: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


class PositionCreate(BaseModel):
    email: str
    pool_address: str
    token0: str
    token1: str
    liquidity: Decimal
    balance: Decimal


class UserCreate(BaseModel):
    wallet_address: str
    email: str
    full_name: str
    password_hash: str
    status: str = "ACTIVE"


class UserStatusUpdate(BaseModel):
    status: str


def item_to_dict(item: dict) -> dict:
    """Flatten a DynamoDB typed item into plain Python values for responses.

    Internal id/log_id/user_id are never exposed to callers.
    """

    def val(v: dict):
        if "S" in v:
            return v["S"]
        if "N" in v:
            return v["N"]
        if "SS" in v:
            return v["SS"]
        if "NULL" in v:
            return None
        return v

    return {k: val(v) for k, v in item.items() if k not in HIDDEN_FIELDS}


HIDDEN_FIELDS = {"id", "log_id", "user_id", "password_hash", "session_id"}
