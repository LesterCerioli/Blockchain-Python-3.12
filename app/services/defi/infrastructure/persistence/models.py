import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ResearchReportModel(Base):

    __tablename__ = "research_reports"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )
    slug: Mapped[str] = mapped_column(String(250), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    categories: Mapped[list[str]] = mapped_column(
        Text, nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(
        Text, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    author_type: Mapped[str] = mapped_column(String(20), nullable=False)
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR(), nullable=False, server_default=text("''::tsvector")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
