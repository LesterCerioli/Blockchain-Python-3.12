from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import text

from .database import Database


class PlatformSecretsService:

    def __init__(self, db: Database) -> None:
        self._db = db

    async def create(
        self,
        key_name: str,
        value_enc: str,
        updated_by: str,
        description: Optional[str] = None,
    ) -> dict:
        sql = text("""
            INSERT INTO platform_secrets
                (id, key_name, value_enc, description, updated_by, created_at, updated_at)
            VALUES
                (:id, :key_name, :value_enc, :description, :updated_by, :created_at, :updated_at)
            RETURNING id, key_name, description, updated_by, created_at, updated_at
        """)
        now = datetime.now(tz=timezone.utc)
        async with self._db.session() as session:
            result = await session.execute(sql, {
                "id": str(uuid4()),
                "key_name": key_name,
                "value_enc": value_enc,
                "description": description,
                "updated_by": updated_by,
                "created_at": now,
                "updated_at": now,
            })
            return dict(result.mappings().one())

    async def update(
        self,
        key_name: str,
        value_enc: str,
        updated_by: str,
        description: Optional[str] = None,
    ) -> Optional[dict]:
        sql = text("""
            UPDATE platform_secrets
            SET value_enc   = :value_enc,
                updated_by  = :updated_by,
                updated_at  = :updated_at,
                description = COALESCE(:description, description)
            WHERE key_name = :key_name
            RETURNING id, key_name, description, updated_by, created_at, updated_at
        """)
        async with self._db.session() as session:
            result = await session.execute(sql, {
                "key_name": key_name,
                "value_enc": value_enc,
                "updated_by": updated_by,
                "updated_at": datetime.now(tz=timezone.utc),
                "description": description,
            })
            row = result.mappings().one_or_none()
            return dict(row) if row else None

    async def delete(self, key_name: str) -> bool:
        sql = text("""
            DELETE FROM platform_secrets
            WHERE key_name = :key_name
            RETURNING id
        """)
        async with self._db.session() as session:
            result = await session.execute(sql, {"key_name": key_name})
            return result.one_or_none() is not None

    async def list_all(self) -> list[dict]:
        sql = text("""
            SELECT id, key_name, description, updated_by, created_at, updated_at
            FROM platform_secrets
            ORDER BY key_name ASC
        """)
        async with self._db.session() as session:
            result = await session.execute(sql)
            return [dict(row) for row in result.mappings().all()]

    async def get_by_key_name(self, key_name: str) -> Optional[dict]:
        sql = text("""
            SELECT id, key_name, description, updated_by, created_at, updated_at
            FROM platform_secrets
            WHERE key_name = :key_name
        """)
        async with self._db.session() as session:
            result = await session.execute(sql, {"key_name": key_name})
            row = result.mappings().one_or_none()
            return dict(row) if row else None
