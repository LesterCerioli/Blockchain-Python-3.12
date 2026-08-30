from pydantic_settings import BaseSettings, SettingsConfigDict


class TokenizationSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TOKENIZATION_", env_file=".env", extra="ignore"
    )

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/fastchainbank"
    )
    dynamodb_endpoint: str = "http://localhost:4566"
    dynamodb_region: str = "us-east-1"
    audit_log_enabled: bool = True
