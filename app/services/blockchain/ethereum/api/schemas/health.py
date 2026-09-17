from pydantic import BaseModel


class ProviderHealthSchema(BaseModel):
    provider_name: str
    is_healthy: bool
    block_height: int | None = None
    latency_ms: float | None = None
    last_error: str | None = None
    is_stale: bool = False


class HealthResponse(BaseModel):
    overall_healthy: bool
    current_block_height: int | None = None
    providers: list[ProviderHealthSchema]
