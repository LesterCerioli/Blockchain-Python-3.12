from __future__ import annotations

from datetime import datetime

from sqlalchemy import text

from ...domain.entities.business_type import BusinessType
from ...domain.entities.tokenization_choice import TokenizationChoice
from ...domain.interfaces.choice_repository import IChoiceRepository
from .database import TokenizationDatabase


def _parse_dt(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return datetime.utcnow()


class PostgresChoiceRepository(IChoiceRepository):
    """Postgres persistence for TokenizationChoice using NATIVE SQL with bound parameters.

    All queries use `text()` + `:param` binding to prevent SQL injection.
    Table: tokenization_choices (see migrations/tokenization/002_create_choices.sql)
    """

    def __init__(self, database: TokenizationDatabase) -> None:
        self._db = database

    async def save(self, choice: TokenizationChoice) -> None:
        # NATIVE SQL with parameters — no string interpolation
        stmt = text(
            """
            INSERT INTO tokenization_choices (id, user_id, business_type, description_tokenization, tokenization_template, chosen_at)
            VALUES (:id, :user_id, :business_type, :description_tokenization, :tokenization_template, :chosen_at)
            ON CONFLICT (id) DO UPDATE
            SET business_type = EXCLUDED.business_type,
                description_tokenization = EXCLUDED.description_tokenization,
                tokenization_template = EXCLUDED.tokenization_template,
                chosen_at = EXCLUDED.chosen_at
            """
        )
        async with self._db.session() as session:
            await session.execute(
                stmt,
                {
                    "id": choice.id,
                    "user_id": choice.user_id,
                    "business_type": choice.business_type.value,
                    "description_tokenization": choice.description_tokenization,
                    "tokenization_template": choice.tokenization_template,
                    "chosen_at": _parse_dt(choice.chosen_at),
                },
            )

    async def list_by_user(self, user_id: str) -> list[TokenizationChoice]:
        stmt = text(
            """
            SELECT id, user_id, business_type, description_tokenization, tokenization_template, chosen_at
            FROM tokenization_choices
            WHERE user_id = :user_id
            ORDER BY chosen_at DESC
            """
        )
        async with self._db.session() as session:
            result = await session.execute(stmt, {"user_id": user_id})
            rows = result.mappings().all()
            return [
                TokenizationChoice(
                    id=str(r["id"]),
                    user_id=r["user_id"],
                    business_type=BusinessType(r["business_type"]),
                    description_tokenization=r["description_tokenization"],
                    tokenization_template=r["tokenization_template"],
                    chosen_at=r["chosen_at"].isoformat() if hasattr(r["chosen_at"], "isoformat") else str(r["chosen_at"]),
                )
                for r in rows
            ]

    async def get_by_id(self, user_id: str, choice_id: str) -> TokenizationChoice | None:
        stmt = text(
            """
            SELECT id, user_id, business_type, description_tokenization, tokenization_template, chosen_at
            FROM tokenization_choices
            WHERE id = :choice_id AND user_id = :user_id
            LIMIT 1
            """
        )
        async with self._db.session() as session:
            result = await session.execute(stmt, {"choice_id": choice_id, "user_id": user_id})
            row = result.mappings().first()
            if not row:
                return None
            return TokenizationChoice(
                id=str(row["id"]),
                user_id=row["user_id"],
                business_type=BusinessType(row["business_type"]),
                description_tokenization=row["description_tokenization"],
                tokenization_template=row["tokenization_template"],
                chosen_at=row["chosen_at"].isoformat() if hasattr(row["chosen_at"], "isoformat") else str(row["chosen_at"]),
            )
