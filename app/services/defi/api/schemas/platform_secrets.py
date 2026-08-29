from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PlatformSecretCreate(BaseModel):
    key_name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Logical key name (snake_case). Maps to DEFI_<KEY_NAME> env var.",
        examples=["coingecko_api_key"],
    )
    value: str = Field(
        min_length=1,
        description="Secret value. Never returned in any response.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Human-readable note about the purpose of this secret.",
    )
    updated_by: str = Field(
        min_length=1,
        max_length=200,
        description="E-mail or identifier of the administrator performing this action.",
    )


class PlatformSecretUpdate(BaseModel):
    value: str = Field(
        min_length=1,
        description="New secret value. Never returned in any response.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Updated note. If omitted the existing description is preserved.",
    )
    updated_by: str = Field(
        min_length=1,
        max_length=200,
        description="E-mail or identifier of the administrator performing this action.",
    )


class PlatformSecretResponse(BaseModel):
    id: UUID
    key_name: str
    description: Optional[str]
    updated_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
