from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeFiSettings(BaseSettings):
    
    model_config = SettingsConfigDict(
        env_prefix="DEFI_", env_file=".env", extra="ignore"
    )

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cryptobank"
    cache_url: str = "redis://localhost:6379/1"

    supported_chain_ids: list[int] = Field(default=[1, 137, 42161])

    price_oracle_url: str = "https://api.coingecko.com/api/v3"
    price_cache_ttl_seconds: int = 30

    market_data_refresh_interval_seconds: int = 60
    indexer_start_block: int = 0
    compliance_screening_enabled: bool = False
    audit_log_enabled: bool = True

    default_slippage_bps: int = Field(default=50, ge=0, le=10_000)
    max_slippage_bps: int = Field(default=500, ge=0, le=10_000)
