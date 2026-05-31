from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EthereumSettings(BaseSettings):
    """
    All configuration for the Ethereum service loaded from environment variables
    or a .env file (network/chain config lives here, not in code).
    """

    model_config = SettingsConfigDict(env_prefix="ETH_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cryptobank"
    stale_block_threshold_seconds: int = 60
    providers: list[dict[str, Any]] = Field(
        default=[
            {
                "name": "primary",
                "url": "http://localhost:8545",
                "priority": 1,
                "request_timeout": 10.0,
                "circuit_breaker_failure_threshold": 5,
                "circuit_breaker_recovery_seconds": 60,
            }
        ]
    )
