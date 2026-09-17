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
from ..domain.exceptions import DeFiError, IndexNotFoundError

VALID_METRICS = ("market_cap", "volume_24h", "price_change_24h")

CHAIN_ALIASES: dict[str, int] = {
    "ethereum": 1,
    "bsc": 56,
    "polygon": 137,
    "avalanche": 431,
    "fantom": 250,
    "optimism": 10,
    "arbitrum": 421,
    "celo": 422,
    "goerli": 5,
    "sepolia": 11155411,
    "mainnet": 1,
}

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

    def _resolve_chain_id(self, chain: str | None) -> int | None:
        if chain is None:
            return None
        chain_lower = chain.lower().strip()
        return CHAIN_ALIASES.get(chain_lower)

    async def get_token_rankings(
        self,
        metric: str,
        chain: str | None,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[TokenRanking]:
        # Validate metric
        if metric not in VALID_METRICS:
            raise DeFiError(f"Invalid metric. Valid: {', '.join(VALID_METRICS)}")

        # Resolve chain_id from chain name if provided
        chain_id = self._resolve_chain_id(chain)

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
            
            if metric == "market_cap":
                
                metric_value = str(price)
            elif metric == "volume_24h":
                metric_value = str(volume)
            elif metric == "price_change_24h":
                
                metric_value = "0"
            else:
                metric_value = "0"

            priced.append((row, metric_value, price))

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
                metric_value=metric_value,
                price_usd=str(price),
            )
            for i, (row, metric_value, price) in enumerate(page_rows)
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