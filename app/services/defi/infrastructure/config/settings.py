import os

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


def database_url_from_env() -> str:
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    name = os.getenv("DB_NAME")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


def _default_chains() -> dict[int, "ChainConfig"]:
    """Canonical chain catalog shipped by default (overridable via DEFI_CHAINS)."""
    return {
        1: ChainConfig(
            name="Ethereum Mainnet",
            rpc_url=os.getenv("DEFI_RPC_1", "https://eth.llamarpc.com"),
            explorer="https://etherscan.io",
        ),
        137: ChainConfig(
            name="Polygon Mainnet",
            rpc_url=os.getenv("DEFI_RPC_137", "https://polygon.llamarpc.com"),
            explorer="https://polygonscan.com",
        ),
        42161: ChainConfig(
            name="Arbitrum One",
            rpc_url=os.getenv("DEFI_RPC_42161", "https://arbitrum.llamarpc.com"),
            explorer="https://arbiscan.io",
        ),
        8453: ChainConfig(
            name="Base",
            rpc_url=os.getenv("DEFI_RPC_8453", "https://base.llamarpc.com"),
            explorer="https://basescan.org",
        ),
        11155111: ChainConfig(
            name="Sepolia Testnet",
            rpc_url=os.getenv("DEFI_RPC_11155111", "https://sepolia.llamarpc.com"),
            explorer="https://sepolia.etherscan.io",
            is_testnet=True,
        ),
        80001: ChainConfig(
            name="Polygon Mumbai Testnet",
            rpc_url=os.getenv("DEFI_RPC_80001", "https://mumbai.llamarpc.com"),
            explorer="https://mumbai.polygonscan.com",
            is_testnet=True,
        ),
    }


class ChainConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    rpc_url: SecretStr
    explorer: str
    is_testnet: bool = False


class DeFiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DEFI_", env_file=".env", extra="ignore"
    )

    cache_url: str = "redis://localhost:6379/1"

    chains: dict[int, ChainConfig] = Field(default_factory=_default_chains)

    supported_chain_ids: list[int] = Field(default=[1, 137, 42161])

    coingecko_api_key: SecretStr | None = None
    cmc_api_key: SecretStr | None = None
    ofac_api_key: SecretStr | None = None

    price_oracle_url: str = "https://api.coingecko.com/api/v3"
    price_cache_ttl_seconds: int = 30

    market_data_refresh_interval_seconds: int = 60
    indexer_start_block: int = 0
    compliance_screening_enabled: bool = False
    sanctioned_addresses: list[str] = Field(default_factory=list)
    audit_log_enabled: bool = True

    default_slippage_bps: int = Field(default=50, ge=0, le=10_000)
    max_slippage_bps: int = Field(default=500, ge=0, le=10_000)

    @model_validator(mode="after")
    def _validate_supported_chain_ids(self) -> "DeFiSettings":
        available = set(self.chains)
        unsupported = [cid for cid in self.supported_chain_ids if cid not in available]
        if unsupported:
            raise ValueError(
                f"Unsupported chain_id(s) in supported_chain_ids: {unsupported}. "
                f"Available chains: {sorted(available)}"
            )
        return self