from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BitcoinSettings(BaseSettings):
    
    model_config = SettingsConfigDict(env_prefix="BTC_", env_file=".env", extra="ignore")

    rpc_url: str = "http://localhost:18443"
    rpc_user: str
    rpc_password: SecretStr
    rpc_wallet: str = ""
    request_timeout: float = 10.0
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_seconds: int = 60
    stale_block_threshold_seconds: int = 120
