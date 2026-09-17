from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TokenizationSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TOKENIZATION_", env_file=".env", extra="ignore"
    )

    
    database_url: SecretStr | None = None
    dynamodb_endpoint: str = "http://localhost:4566"
    dynamodb_region: str = "us-east-1"
    audit_log_enabled: bool = True
    groq_api_key: SecretStr | None = None
    groq_api_url: str = "https://api.groq.com/openai/v1/chat/completions"
    groq_model: str = "llama-3.1-70b-versatile"
    groq_timeout_seconds: int = 10
    groq_enabled: bool = True
    
    llm_provider: str = "groq"
    grok_api_key: SecretStr | None = None
    grok_api_url: str = "https://api.x.ai/v1/chat/completions"
    grok_model: str = "grok-2-latest"
    grok_timeout_seconds: int = 15
    grok_enabled: bool = True

    @field_validator(
        "database_url", "groq_api_key", "grok_api_key",
        mode="before",
    )
    @classmethod
    def _empty_str_to_none(cls, v):
        
        if isinstance(v, str) and not v.strip():
            return None
        return v
