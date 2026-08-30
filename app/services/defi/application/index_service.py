import os
from decimal import Decimal

import asyncpg

from app.services.aux.infrastructure.dynamodb_client import (
    TABLE_TOKEN_META,
    DynamoDBClient,
)

from ..domain.entities.index import (
    MarketIndex,
    PaginatedResponse,
    ProtocolRanking,
    TokenRanking,
)
from ..domain.exceptions import IndexNotFoundError

DEFAULT_DSN = "postgresql+asyncpg://postgres:postgres@localhost:5432/blockchain_db"

INDEX_CATALOG: list[MarketIndex] = [
    MarketIndex(
        code="defi-tvl-top20",
        name="DeFi TVL Top 20",
        description="Top 20 protocols ranked by total value locked",
        category="tvl",
    ),
    MarketIndex(
        code="top100-market-cap",
        name="Top 100 by Market Cap",
        description="Top 100 tokens ranked by market cap (proxy: current price from token_meta)",
        category="market_cap",
    ),
]


class IndexService:
    def __init__(
        self,
        database_url: str | None = None,
        dynamodb: DynamoDBClient | None = None,
    ) -> None:
        self._dsn = database_url or os.environ.get("DEFI_DATABASE_URL") or DEFAULT_DSN
        self._ddb = dynamodb or DynamoDBClient()

    async def list_indices(self) -> list[MarketIndex]:
        return list(INDEX_CATALOG)

    async def get_index(self, code: str) -> MarketIndex:
        for index in INDEX_CATALOG:
            if index.code == code:
                return index
        raise IndexNotFoundError(code)

    async def get_token_rankings(
        self,
        metric: str,
        chain_id: int | None,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[TokenRanking]:
        dsn = self._dsn.replace("+asyncpg", "")
        async with await asyncpg.connect(dsn) as conn:
            if chain_id is not None:
                rows = await conn.fetch(
                    "SELECT address, symbol, name, decimals, chain_id "
                    "FROM tokens WHERE chain_id = $1",
                    chain_id,
                )
            else:
                rows = await conn.fetch(
                    "SELECT address, symbol, name, decimals, chain_id FROM tokens"
                )

        priced: list[tuple] = []
        for row in rows:
            meta = self._ddb.query_index(
                TABLE_TOKEN_META, "symbol_index", "symbol", row["symbol"]
            )
            price = (
                Decimal(meta[0]["current_price"]["N"])
                if meta and "current_price" in meta[0]
                else Decimal(0)
            )
            volume = (
                Decimal(meta[0]["volume_24h"]["N"])
                if meta and "volume_24h" in meta[0]
                else Decimal(0)
            )
            value = price if metric in ("price", "market_cap") else volume
            priced.append((row, value))

        priced.sort(key=lambda item: item[1], reverse=True)
        total = len(priced)
        start = (page - 1) * page_size
        page_rows = priced[start : start + page_size]

        items = [
            TokenRanking(
                rank=start + 1 + i,
                symbol=row["symbol"],
                name=row["name"],
                chain_id=row["chain_id"],
                metric=metric,
                value=value,
            )
            for i, (row, value) in enumerate(page_rows)
        ]
        return PaginatedResponse(
            items=items, page=page, page_size=page_size, total=total
        )

    async def get_protocol_rankings(
        self,
        metric: str,
        chain_id: int | None = None,
    ) -> list[ProtocolRanking]:
        dsn = self._dsn.replace("+asyncpg", "")
        async with await asyncpg.connect(dsn) as conn:
            if chain_id is not None:
                rows = await conn.fetch(
                    "SELECT protocol, chain_id, SUM(liquidity) AS tvl "
                    "FROM pools WHERE chain_id = $1 "
                    "GROUP BY protocol, chain_id ORDER BY tvl DESC",
                    chain_id,
                )
            else:
                rows = await conn.fetch(
                    "SELECT protocol, chain_id, SUM(liquidity) AS tvl "
                    "FROM pools GROUP BY protocol, chain_id ORDER BY tvl DESC"
                )

        return [
            ProtocolRanking(
                rank=i + 1,
                protocol=row["protocol"],
                chain_id=row["chain_id"],
                metric=metric,
                value=Decimal(row["tvl"]),
            )
            for i, row in enumerate(rows)
        ]
