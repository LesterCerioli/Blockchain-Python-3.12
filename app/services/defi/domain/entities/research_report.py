import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class ResearchReport(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    summary: str
    target_token: str
    price_target: Decimal = Field(ge=0)
    published_at: datetime

    @field_validator("title", "summary")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must not be blank")
        return v

    @field_validator("target_token")
    @classmethod
    def normalize_token(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("target_token must not be blank")
        return v.upper()

    model_config = {"frozen": True}
