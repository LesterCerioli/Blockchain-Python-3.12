from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class NodeHealth:
    node_name: str
    is_healthy: bool
    block_height: int | None = None
    latency_ms: float | None = None
    last_error: str | None = None
    is_stale: bool = False


class IHealthMonitor(ABC):

    @abstractmethod
    async def check_health(self) -> list[NodeHealth]: ...

    @abstractmethod
    async def get_current_block_height(self) -> int | None: ...
