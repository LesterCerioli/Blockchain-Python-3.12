from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

from .business_type import BusinessType


class TokenizationChoice(BaseModel):
    id: str = Field(..., description="Choice record id")
    user_id: str = Field(..., min_length=1, description="Owner user_id - isolation mandatory")
    business_type: BusinessType = Field(..., description="Selected business sector")
    description_tokenization: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Challenge/objective text",
    )
    tokenization_template: str = Field(
        ...,
        min_length=1,
        description="Chosen template name or custom reference",
    )
    chosen_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of choice",
    )

    model_config = {"frozen": True}

    @field_validator("user_id", "tokenization_template")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @field_validator("description_tokenization")
    @classmethod
    def desc_not_blank(cls, v: str) -> str:
        if not v.strip() or len(v.strip()) < 10:
            raise ValueError("description_tokenization must be >=10 chars")
        return v.strip()
