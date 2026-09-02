import os

from fastapi import Request

from ..application.chain_config_service import ChainConfigService
from ..application.index_service import IndexService
from ..application.quote_service import QuoteService
from ..domain.interfaces.ohlcv_repository import IOHLCVRepository
from ..infrastructure.config.settings import DeFiSettings
from ..infrastructure.persistence.database import Database
from ..infrastructure.persistence.platform_secrets_service import PlatformSecretsService


def _get_database_url() -> str:
    dsn = os.getenv("DEFI_DATABASE_URL")
    if dsn:
        return dsn
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    name = os.getenv("DB_NAME", "blockchain_db")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


def get_quote_service(request: Request) -> QuoteService:
    return request.app.state.defi_quote_service


def get_market_quote_service(request: Request) -> QuoteService:
    return request.app.state.defi_quote_service


def get_platform_secrets_service(request: Request) -> PlatformSecretsService:
    db = Database(_get_database_url())
    return PlatformSecretsService(db)


def get_chain_config_service(request: Request) -> ChainConfigService:
    settings = DeFiSettings()
    return ChainConfigService(settings)


def get_ohlcv_repository(request: Request) -> IOHLCVRepository:
    return request.app.state.defi_ohlcv_repository


def get_index_service() -> IndexService:
    return IndexService()
