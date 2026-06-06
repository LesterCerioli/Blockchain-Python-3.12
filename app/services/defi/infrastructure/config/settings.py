from typing import Optional

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChainConfig(BaseModel):
    name: str
    rpc_url: SecretStr
    explorer: str
    is_testnet: bool = False

    model_config = {"frozen": True}


class DeFiSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_prefix="DEFI_", env_file=".env", extra="ignore"
    )

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cryptobank"
    cache_url: str = "redis://localhost:6379/1"

    supported_chain_ids: list[int] = Field(default=[1, 137, 42161])

    chains: dict[int, ChainConfig] = Field(
        default_factory=lambda: {
            1: ChainConfig(
                name="Ethereum",
                rpc_url="https://eth.llamarpc.com",
                explorer="https://etherscan.io",
            ),
            137: ChainConfig(
                name="Polygon",
                rpc_url="https://polygon.llamarpc.com",
                explorer="https://polygonscan.com",
            ),
            42161: ChainConfig(
                name="Arbitrum One",
                rpc_url="https://arb1.arbitrum.io/rpc",
                explorer="https://arbiscan.io",
            ),
            8453: ChainConfig(
                name="Base",
                rpc_url="https://mainnet.base.org",
                explorer="https://basescan.org",
            ),
            11155111: ChainConfig(
                name="Sepolia",
                rpc_url="https://rpc.sepolia.org",
                explorer="https://sepolia.etherscan.io",
                is_testnet=True,
            ),
            80001: ChainConfig(
                name="Mumbai",
                rpc_url="https://rpc-mumbai.maticvigil.com",
                explorer="https://mumbai.polygonscan.com",
                is_testnet=True,
            ),
        }
    )

    price_oracle_url: str = "https://api.coingecko.com/api/v3"
    price_cache_ttl_seconds: int = 30

    market_data_refresh_interval_seconds: int = 60
    indexer_start_block: int = 0
    compliance_screening_enabled: bool = False
    audit_log_enabled: bool = True

    default_slippage_bps: int = Field(default=50, ge=0, le=10_000)
    max_slippage_bps: int = Field(default=500, ge=0, le=10_000)

    coingecko_api_key: Optional[SecretStr] = None
    cmc_api_key: Optional[SecretStr] = None
    redis_url: str = "redis://localhost:6379/0"
    quote_cache_ttl_seconds: int = 30
    history_cache_ttl_seconds: int = 300
    market_data_timeout_seconds: int = 10
    max_symbols_per_batch: int = 100
    ofac_api_key: Optional[SecretStr] = None
