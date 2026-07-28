import uuid
from typing import Any, Optional

from ..domain.entities.research_report import ResearchReport
from ..domain.exceptions import ResearchReportNotFoundError
from ..domain.interfaces.research_report_repository import IResearchReportRepository

FORBIDDEN_FIELDS = {"user_id", "wallet_address", "subscriber_id", "personalized_for"}


class ResearchReportService:

    def __init__(self, repository: IResearchReportRepository) -> None:
        self._repository = repository

    async def publish(self, payload: dict[str, Any]) -> ResearchReport:
        for field in FORBIDDEN_FIELDS:
            if field in payload:
                raise ValueError(
                    f"{field} is forbidden in research report payloads — "
                    "reports are impersonal and must not be personalized"
                )

        if "author_type" in payload and payload["author_type"] == "user":
            raise ValueError(
                'author_type must be "editorial" or "automated", never "user"'
            )

        report = ResearchReport.model_validate(payload)
        await self._repository.upsert(report)
        return report

    async def get_by_id(self, report_id: uuid.UUID) -> ResearchReport:
        report = await self._repository.get_by_id(report_id)
        if report is None:
            raise ResearchReportNotFoundError(str(report_id))
        return report

    async def get_by_slug(self, slug: str) -> ResearchReport:
        report = await self._repository.get_by_slug(slug)
        if report is None:
            raise ResearchReportNotFoundError(slug)
        return report

    async def list_by_category(self, category: str) -> list[ResearchReport]:
        return await self._repository.list_by_category(category)

    async def list_by_tag(self, tag: str) -> list[ResearchReport]:
        return await self._repository.list_by_tag(tag)

    async def search(self, query: str, limit: int = 20) -> list[ResearchReport]:
        return await self._repository.search_fts(query, limit=limit)

    async def delete(self, report_id: uuid.UUID) -> None:
        await self._repository.delete(report_id)

    async def delete_by_slug(self, slug: str) -> None:
        await self._repository.delete_by_slug(slug)
