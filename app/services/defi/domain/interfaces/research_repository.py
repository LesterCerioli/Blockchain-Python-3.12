import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from ..entities.research_report import ResearchReport


class IResearchRepository(ABC):

    @abstractmethod
    async def save(self, report: ResearchReport) -> None: ...

    @abstractmethod
    async def get_by_id(self, report_id: uuid.UUID) -> Optional[ResearchReport]: ...

    @abstractmethod
    async def get_by_token(self, target_token: str) -> list[ResearchReport]: ...

    @abstractmethod
    async def list_all(self) -> list[ResearchReport]: ...

    @abstractmethod
    async def list_by_date_range(
        self,
        from_date: datetime,
        to_date: datetime,
    ) -> list[ResearchReport]:
        """Returns reports whose published_at falls within the given range (inclusive)."""
        ...

    @abstractmethod
    async def delete(self, report_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def count(self) -> int: ...
