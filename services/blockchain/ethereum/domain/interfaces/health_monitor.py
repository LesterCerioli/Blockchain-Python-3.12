from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ProviderHealth:
    provider_name: str
    is_healthy: bool
    block_height: int | None = None
    latency_ms: float | None = None
    last_error: str | None = None
    is_stale: bool = False


class IHealthMonitor(ABC):
    """Port: contract for checking provider and chain health."""

    @abstractmethod
    async def check_health(self) -> list[ProviderHealth]: ...

    @abstractmethod
    async def get_current_block_height(self) -> int | None: ...
