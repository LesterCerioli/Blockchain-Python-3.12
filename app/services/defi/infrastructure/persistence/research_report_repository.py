import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert

from ...domain.entities.research_report import ResearchReport
from ...domain.interfaces.research_report_repository import IResearchReportRepository
from .database import Database
from .models import ResearchReportModel


class PostgresResearchReportRepository(IResearchReportRepository):

    def __init__(self, db: Database) -> None:
        self._db = db

    async def get_by_id(self, report_id: UUID) -> Optional[ResearchReport]:
        async with self._db.session() as session:
            result = await session.execute(
                select(ResearchReportModel).where(ResearchReportModel.report_id == report_id)
            )
            row = result.scalar_one_or_none()
            return self._to_entity(row) if row else None

    async def get_by_slug(self, slug: str) -> Optional[ResearchReport]:
        async with self._db.session() as session:
            result = await session.execute(
                select(ResearchReportModel).where(ResearchReportModel.slug == slug)
            )
            row = result.scalar_one_or_none()
            return self._to_entity(row) if row else None

    async def list_by_category(self, category: str) -> list[ResearchReport]:
        async with self._db.session() as session:
            result = await session.execute(
                select(ResearchReportModel).where(
                    ResearchReportModel.categories.contains(category)
                )
            )
            return [self._to_entity(row) for row in result.scalars().all()]

    async def list_by_tag(self, tag: str) -> list[ResearchReport]:
        async with self._db.session() as session:
            result = await session.execute(
                select(ResearchReportModel).where(
                    ResearchReportModel.tags.contains(tag)
                )
            )
            return [self._to_entity(row) for row in result.scalars().all()]

    async def search_fts(self, query: str, limit: int = 20) -> list[ResearchReport]:
        async with self._db.session() as session:
            stmt = (
                select(ResearchReportModel)
                .where(
                    ResearchReportModel.search_vector.op("@@")(
                        func.plainto_tsquery("english", text(":query"))
                    )
                )
                .order_by(
                    func.ts_rank(
                        ResearchReportModel.search_vector,
                        func.plainto_tsquery("english", text(":query")),
                    ).desc()
                )
                .limit(limit)
            )
            result = await session.execute(stmt, {"query": query})
            return [self._to_entity(row) for row in result.scalars().all()]

    async def upsert(self, report: ResearchReport) -> None:
        now = datetime.now(tz=timezone.utc)
        search_text = self._build_search_text(report)
        stmt = (
            insert(ResearchReportModel)
            .values(
                report_id=report.report_id,
                slug=report.slug,
                title=report.title,
                body_markdown=report.body_markdown,
                summary=report.summary,
                published_at=report.published_at,
                categories=json.dumps(report.categories),
                tags=json.dumps(report.tags),
                version=report.version,
                author_type=report.author_type,
                search_vector=search_text,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["report_id"],
                set_={
                    "slug": report.slug,
                    "title": report.title,
                    "body_markdown": report.body_markdown,
                    "summary": report.summary,
                    "published_at": report.published_at,
                    "categories": json.dumps(report.categories),
                    "tags": json.dumps(report.tags),
                    "version": report.version,
                    "author_type": report.author_type,
                    "search_vector": search_text,
                    "updated_at": now,
                },
            )
        )
        async with self._db.session() as session:
            await session.execute(stmt)

    async def delete(self, report_id: UUID) -> None:
        async with self._db.session() as session:
            await session.execute(
                ResearchReportModel.__table__.delete().where(
                    ResearchReportModel.report_id == report_id
                )
            )

    async def delete_by_slug(self, slug: str) -> None:
        async with self._db.session() as session:
            await session.execute(
                ResearchReportModel.__table__.delete().where(
                    ResearchReportModel.slug == slug
                )
            )

    @staticmethod
    def _build_search_text(report: ResearchReport) -> str:
        parts = [
            report.title,
            report.summary,
            report.body_markdown,
            *report.categories,
            *report.tags,
        ]
        return " ".join(parts)

    @staticmethod
    def _to_entity(row: ResearchReportModel) -> ResearchReport:
        return ResearchReport(
            report_id=row.report_id,
            slug=row.slug,
            title=row.title,
            body_markdown=row.body_markdown,
            summary=row.summary,
            published_at=row.published_at,
            categories=json.loads(row.categories),
            tags=json.loads(row.tags),
            version=row.version,
            author_type=row.author_type,
        )
