from uuid import UUID

import asyncpg

from app.services.defi.domain.entities.pool import Pool


class InMemoryPoolRepository:
    """Pool repository using PostgreSQL backend (not truly in-memory)."""

    def __init__(self, database_url: str | None = None) -> None:
        self._dsn = (
            database_url
            or "postgresql+asyncpg://postgres:postgres@localhost:5432/blockchain_db"
        )

    async def _get_connection(self):
        return await asyncpg.connect(self._dsn)

    async def get_by_address(self, address: str) -> Pool | None:
        async with await self._get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, address, token0_address, token1_address, fee_bps, protocol, chain_id, liquidity FROM pools WHERE address = $1",
                address.lower(),
            )
            if row is None:
                return None
            # Fetch token entities separately or construct minimal Pool
            from uuid import UUID

            from app.services.defi.domain.entities.token import Token

            return Pool(
                id=UUID(str(row["id"])),
                address=row["address"],
                token0=Token(
                    id=UUID("00000000-0000-0000-0000-000000000000"),
                    address=row["token0_address"],
                    symbol="",
                    name="",
                    decimals=18,
                    chain_id=row["chain_id"],
                ),
                token1=Token(
                    id=UUID("00000000-0000-0000-0000-000000000000"),
                    address=row["token1_address"],
                    symbol="",
                    name="",
                    decimals=18,
                    chain_id=row["chain_id"],
                ),
                fee_bps=row["fee_bps"],
                protocol=row["protocol"],
                chain_id=row["chain_id"],
                liquidity=row["liquidity"],
            )

    async def list_by_tokens(
        self, token0: str, token1: str, chain_id: int
    ) -> list[Pool]:
        async with await self._get_connection() as conn:
            rows = await conn.fetch(
                "SELECT id, address, token0_address, token1_address, fee_bps, protocol, chain_id, liquidity FROM pools WHERE chain_id = $1 AND token0_address = $2 AND token1_address = $3",
                chain_id,
                token0.lower(),
                token1.lower(),
            )
            return [
                InMemoryPoolRepository._make_pool_from_row(self, row) for row in rows
            ]

    async def upsert(self, pool: Pool) -> None:
        async with await self._get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO pools (id, address, token0_address, token1_address, fee_bps, protocol, chain_id, liquidity)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (address) DO UPDATE SET
                    token0_address = EXCLUDED.token0_address,
                    token1_address = EXCLUDED.token1_address,
                    fee_bps = EXCLUDED.fee_bps,
                    protocol = EXCLUDED.protocol,
                    chain_id = EXCLUDED.chain_id,
                    liquidity = EXCLUDED.liquidity,
                    updated_at = NOW()
                """,
                str(pool.id),
                pool.address.lower(),
                pool.token0.address.lower(),
                pool.token1.address.lower(),
                pool.fee_bps,
                pool.protocol,
                pool.chain_id,
                pool.liquidity,
            )

    async def add(self, pool: Pool) -> None:
        await self.upsert(pool)

    @staticmethod
    def _make_pool_from_row(row) -> Pool:
        from app.services.defi.domain.entities.token import Token

        return Pool(
            id=UUID(str(row["id"])),
            address=row["address"],
            token0=Token(
                id=UUID("00000000-0000-0000-0000-000000000000"),
                address=row["token0_address"],
                symbol="",
                name="",
                decimals=18,
                chain_id=row["chain_id"],
            ),
            token1=Token(
                id=UUID("00000000-0000-0000-0000-000000000000"),
                address=row["token1_address"],
                symbol="",
                name="",
                decimals=18,
                chain_id=row["chain_id"],
            ),
            fee_bps=row["fee_bps"],
            protocol=row["protocol"],
            chain_id=row["chain_id"],
            liquidity=row["liquidity"],
        )
