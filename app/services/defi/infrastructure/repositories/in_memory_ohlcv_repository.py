from datetime import datetime

import asyncpg

from app.services.defi.domain.value_objects.ohlcv import OHLCVCandle


class InMemoryOHLCVRepository:
    """OHLCV repository using PostgreSQL backend (not truly in-memory)."""

    def __init__(self, database_url: str | None = None) -> None:
        self._dsn = (
            database_url
            or "postgresql+asyncpg://postgres:postgres@localhost:5432/blockchain_db"
        )

    async def _get_connection(self):
        return await asyncpg.connect(self._dsn)

    async def get_ohlcv(
        self,
        symbol: str,
        interval: str,
        from_ts: datetime,
        to_ts: datetime,
    ) -> list[OHLCVCandle]:
        async with await self._get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, symbol, interval, open_time, open, high, low, close, volume
                FROM ohlcv_candles
                WHERE symbol = $1 AND interval = $2 AND open_time >= $3 AND open_time <= $4
                ORDER BY open_time
                """,
                symbol.upper(),
                interval,
                from_ts,
                to_ts,
            )
            return [
                OHLCVCandle(
                    open_time=row["open_time"],
                    open=str(row["open"]),
                    high=str(row["high"]),
                    low=str(row["low"]),
                    close=str(row["close"]),
                    volume=str(row["volume"]),
                )
                for row in rows
            ]

    async def add(self, candle: OHLCVCandle) -> None:
        async with await self._get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO ohlcv_candles (symbol, interval, open_time, open, high, low, close, volume)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                candle.symbol.upper(),
                candle.interval,
                candle.open_time,
                float(candle.open),
                float(candle.high),
                float(candle.low),
                float(candle.close),
                float(candle.volume),
            )
