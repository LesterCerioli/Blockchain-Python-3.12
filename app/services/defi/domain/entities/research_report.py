import re
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

FORBIDDEN_FIELDS = {"user_id", "wallet_address", "subscriber_id", "personalized_for"}


def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value


class ResearchReport(BaseModel):

    report_id: UUID
    slug: str = Field(max_length=250, pattern=r"^[a-z0-9-]+$")
    title: str = Field(max_length=200)
    body_markdown: str
    summary: str = Field(max_length=500)
    published_at: datetime
    categories: list[str]
    tags: list[str]
    version: int = Field(ge=1)
    author_type: Literal["editorial", "automated"]

    model_config = {"frozen": True}

    @model_validator(mode="before")
    @classmethod
    def _generate_slug_and_reject_forbidden(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "title" in data and (data.get("slug") is None or data.get("slug") == ""):
                data["slug"] = _slugify(data["title"])
            for field in FORBIDDEN_FIELDS:
                if field in data:
                    raise ValueError(
                        f"{field} is forbidden in ResearchReport — "
                        "reports are impersonal and must not be personalized"
                    )
            if "author_type" in data and data["author_type"] == "user":
                raise ValueError(
                    'author_type must be "editorial" or "automated", never "user"'
                )
        return data

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v

    @field_validator("summary")
    @classmethod
    def summary_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("summary must not be blank")
        return v

    @field_validator("body_markdown")
    @classmethod
    def body_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("body_markdown must not be blank")
        return v

    @field_validator("categories")
    @classmethod
    def categories_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("categories must not be empty")
        return v

    @field_validator("tags")
    @classmethod
    def tags_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("tags must not be empty")
        return v
