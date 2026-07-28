from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ResearchPublishRequest(BaseModel):
    report_id: UUID
    slug: Optional[str] = Field(default=None, max_length=250, pattern=r"^[a-z0-9-]+$")
    title: str = Field(max_length=200)
    body_markdown: str
    summary: str = Field(max_length=500)
    published_at: datetime
    categories: list[str] = Field(min_length=1)
    tags: list[str] = Field(min_length=1)
    version: int = Field(ge=1)
    author_type: Literal["editorial", "automated"]


class ResearchReportResponse(BaseModel):
    slug: str
    title: str
    body_markdown: str
    summary: str
    published_at: datetime
    categories: list[str]
    tags: list[str]
    version: int
    author_type: str


class ResearchListResponse(BaseModel):
    items: list[ResearchReportResponse]
    total: int


class ResearchSearchResponse(BaseModel):
    items: list[ResearchReportResponse]
    total: int
