import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


def database_url_from_env() -> str:
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    name = os.getenv("DB_NAME")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


class ChainConfig(BaseModel):
    chain_id: int
    name: str
    rpc_url: str | None = None
    explorer: str | None = None
    is_testnet: bool = False


class DeFiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DEFI_", env_file=".env", extra="ignore"
    )

    cache_url: str = "redis://localhost:6379/1"

    chains: dict[int, ChainConfig] = Field(default_factory=dict)

    supported_chain_ids: list[int] = Field(default=[1, 137, 42161])

    price_oracle_url: str = "https://api.coingecko.com/api/v3"
    price_cache_ttl_seconds: int = 30

    market_data_refresh_interval_seconds: int = 60
    indexer_start_block: int = 0
    compliance_screening_enabled: bool = False
    sanctioned_addresses: list[str] = Field(default_factory=list)
    audit_log_enabled: bool = True

    default_slippage_bps: int = Field(default=50, ge=0, le=10_000)
    max_slippage_bps: int = Field(default=500, ge=0, le=10_000)
