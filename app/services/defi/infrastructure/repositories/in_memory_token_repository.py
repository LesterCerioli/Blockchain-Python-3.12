from uuid import UUID

import asyncpg

from app.services.defi.domain.entities.token import Token


class InMemoryTokenRepository:
    """Token repository using PostgreSQL backend (not truly in-memory)."""

    def __init__(self, database_url: str | None = None) -> None:
        self._dsn = (
            database_url
            or "postgresql+asyncpg://postgres:postgres@localhost:5432/blockchain_db"
        )

    async def _get_connection(self):
        return await asyncpg.connect(self._dsn)

    async def get_by_address(self, address: str, chain_id: int) -> Token | None:
        async with await self._get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, address, symbol, name, decimals, chain_id FROM tokens WHERE address = $1 AND chain_id = $2",
                address.lower(),
                chain_id,
            )
            if row is None:
                return None
            return Token(
                id=UUID(str(row["id"])),
                address=row["address"],
                symbol=row["symbol"],
                name=row["name"],
                decimals=row["decimals"],
                chain_id=row["chain_id"],
            )

    async def list_by_chain(self, chain_id: int) -> list[Token]:
        async with await self._get_connection() as conn:
            rows = await conn.fetch(
                "SELECT id, address, symbol, name, decimals, chain_id FROM tokens WHERE chain_id = $1",
                chain_id,
            )
            return [
                Token(
                    id=UUID(str(row["id"])),
                    address=row["address"],
                    symbol=row["symbol"],
                    name=row["name"],
                    decimals=row["decimals"],
                    chain_id=row["chain_id"],
                )
                for row in rows
            ]

    async def upsert(self, token: Token) -> None:
        async with await self._get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO tokens (id, address, symbol, name, decimals, chain_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (address, chain_id) DO UPDATE SET
                    symbol = EXCLUDED.symbol,
                    name = EXCLUDED.name,
                    decimals = EXCLUDED.decimals,
                    chain_id = EXCLUDED.chain_id,
                    updated_at = NOW()
                """,
                str(token.id),
                token.address.lower(),
                token.symbol,
                token.name,
                token.decimals,
                token.chain_id,
            )

    async def add(self, token: Token) -> None:
        await self.upsert(token)
