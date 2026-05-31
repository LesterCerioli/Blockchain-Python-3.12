from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


class Database:
    """
    Async SQLAlchemy engine wrapper with session factory (SRP: only manages
    the connection pool and session lifecycle).
    """

    def __init__(self, url: str) -> None:
        self._engine = create_async_engine(url, pool_pre_ping=True, echo=False)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self) -> None:
        await self._engine.dispose()
