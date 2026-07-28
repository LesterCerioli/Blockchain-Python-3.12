import uuid
from abc import ABC, abstractmethod
from typing import Optional

from ..entities.research_report import ResearchReport


class IResearchReportRepository(ABC):

    @abstractmethod
    async def get_by_id(self, report_id: uuid.UUID) -> Optional[ResearchReport]: ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[ResearchReport]: ...

    @abstractmethod
    async def list_by_category(self, category: str) -> list[ResearchReport]: ...

    @abstractmethod
    async def list_by_tag(self, tag: str) -> list[ResearchReport]: ...

    @abstractmethod
    async def search_fts(self, query: str, limit: int = 20) -> list[ResearchReport]: ...

    @abstractmethod
    async def upsert(self, report: ResearchReport) -> None: ...

    @abstractmethod
    async def delete(self, report_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def delete_by_slug(self, slug: str) -> None: ...
