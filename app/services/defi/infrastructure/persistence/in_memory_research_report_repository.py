import json
from typing import Optional
from uuid import UUID

from ...domain.entities.research_report import ResearchReport
from ...domain.interfaces.research_report_repository import IResearchReportRepository


class InMemoryResearchReportRepository(IResearchReportRepository):

    def __init__(self) -> None:
        self._store: dict[UUID, ResearchReport] = {}

    async def get_by_id(self, report_id: UUID) -> Optional[ResearchReport]:
        return self._store.get(report_id)

    async def get_by_slug(self, slug: str) -> Optional[ResearchReport]:
        for report in self._store.values():
            if report.slug == slug:
                return report
        return None

    async def delete_by_slug(self, slug: str) -> None:
        keys = [k for k, v in self._store.items() if v.slug == slug]
        for k in keys:
            self._store.pop(k, None)

    async def list_by_category(self, category: str) -> list[ResearchReport]:
        return [r for r in self._store.values() if category in r.categories]

    async def list_by_tag(self, tag: str) -> list[ResearchReport]:
        return [r for r in self._store.values() if tag in r.tags]

    async def search_fts(self, query: str, limit: int = 20) -> list[ResearchReport]:
        q_lower = query.lower()
        results: list[tuple[float, ResearchReport]] = []
        for report in self._store.values():
            text_blob = " ".join(
                [
                    report.title,
                    report.summary,
                    report.body_markdown,
                    *report.categories,
                    *report.tags,
                ]
            ).lower()
            if q_lower in text_blob:
                score = text_blob.count(q_lower)
                results.append((score, report))
        results.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in results[:limit]]

    async def upsert(self, report: ResearchReport) -> None:
        self._store[report.report_id] = report

    async def delete(self, report_id: UUID) -> None:
        self._store.pop(report_id, None)
