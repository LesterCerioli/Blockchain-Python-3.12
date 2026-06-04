import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class BlockchainEvent(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    chain_id: int = Field(gt=0)
    contract_address: str
    block_number: int = Field(ge=0)
    tx_hash: str
    log_index: int = Field(ge=0)
    payload: dict[str, Any]
    emitted_at: datetime

    @field_validator("event_type")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("event_type must not be blank")
        return v

    @field_validator("contract_address", "tx_hash")
    @classmethod
    def normalize_hex(cls, v: str) -> str:
        return v.lower()

    model_config = {"frozen": True}
