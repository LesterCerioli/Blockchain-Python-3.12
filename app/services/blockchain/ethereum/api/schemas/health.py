from typing import Optional

from pydantic import BaseModel


class ProviderHealthSchema(BaseModel):
    provider_name: str
    is_healthy: bool
    block_height: Optional[int] = None
    latency_ms: Optional[float] = None
    last_error: Optional[str] = None
    is_stale: bool = False


class HealthResponse(BaseModel):
    overall_healthy: bool
    current_block_height: Optional[int] = None
    providers: list[ProviderHealthSchema]
