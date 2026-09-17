from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from ...domain.entities.node import NodeRecord, NodeStatus
from ...domain.interfaces.node_repository import INodeRepository
from .database import Database
from .models import BtcNodeModel


class PostgresNodeRepository(INodeRepository):

    def __init__(self, db: Database) -> None:
        self._db = db

    async def get_all(self) -> list[NodeRecord]:
        async with self._db.session() as session:
            result = await session.execute(select(BtcNodeModel))
            return [self._to_entity(row) for row in result.scalars().all()]

    async def get_by_name(self, name: str) -> Optional[NodeRecord]:
        async with self._db.session() as session:
            result = await session.execute(
                select(BtcNodeModel).where(BtcNodeModel.name == name)
            )
            row = result.scalar_one_or_none()
            return self._to_entity(row) if row else None

    async def upsert(self, record: NodeRecord) -> None:
        now = datetime.now(tz=timezone.utc)
        stmt = (
            insert(BtcNodeModel)
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
    def _to_entity(row: BtcNodeModel) -> NodeRecord:
        return NodeRecord(
            id=row.id,
            name=row.name,
            url=row.url,
            priority=row.priority,
            status=NodeStatus(row.status),
            last_seen_block=row.last_seen_block,
            last_checked_at=row.last_checked_at,
        )
