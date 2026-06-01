from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from ...domain.entities.provider import ProviderRecord, ProviderStatus
from ...domain.interfaces.provider_repository import IProviderRepository
from .database import Database
from .models import EthProviderModel


class PostgresProviderRepository(IProviderRepository):
    
    def __init__(self, db: Database) -> None:
        self._db = db

    async def get_all(self) -> list[ProviderRecord]:
        async with self._db.session() as session:
            result = await session.execute(select(EthProviderModel))
            return [self._to_entity(row) for row in result.scalars().all()]

    async def get_by_name(self, name: str) -> Optional[ProviderRecord]:
        async with self._db.session() as session:
            result = await session.execute(
                select(EthProviderModel).where(EthProviderModel.name == name)
            )
            row = result.scalar_one_or_none()
            return self._to_entity(row) if row else None

    async def upsert(self, record: ProviderRecord) -> None:
        now = datetime.now(tz=timezone.utc)
        stmt = (
            insert(EthProviderModel)
            .values(
                name=record.name,
                url=record.url,
                priority=record.priority,
                status=record.status.value,
                last_seen_block=record.last_seen_block,
                last_checked_at=record.last_checked_at,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["name"],
                set_={
                    "url": record.url,
                    "priority": record.priority,
                    "status": record.status.value,
                    "last_seen_block": record.last_seen_block,
                    "last_checked_at": record.last_checked_at,
                    "updated_at": now,
                },
            )
        )
        async with self._db.session() as session:
            await session.execute(stmt)

    @staticmethod
    def _to_entity(row: EthProviderModel) -> ProviderRecord:
        return ProviderRecord(
            id=row.id,
            name=row.name,
            url=row.url,
            priority=row.priority,
            status=ProviderStatus(row.status),
            last_seen_block=row.last_seen_block,
            last_checked_at=row.last_checked_at,
        )
