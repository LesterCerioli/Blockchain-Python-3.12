from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..rpc.circuit_breaker import CircuitBreaker


@dataclass
class NodeConfig:
    name: str
    url: str
    rpc_user: str
    rpc_password: str
    priority: int = 1
    request_timeout: float = 10.0
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_seconds: int = 60


class BaseProvider(ABC):

    def __init__(self, config: NodeConfig) -> None:
        self._config = config
        self._circuit_breaker = CircuitBreaker(
            name=config.name,
            failure_threshold=config.circuit_breaker_failure_threshold,
            recovery_timeout_seconds=config.circuit_breaker_recovery_seconds,
        )

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def url(self) -> str:
        return self._config.url

    @property
    def priority(self) -> int:
        return self._config.priority

    @property
    def is_available(self) -> bool:
        return not self._circuit_breaker.is_open()

    @abstractmethod
    async def get_block_height(self) -> int: ...

    @abstractmethod
    async def get_network(self) -> str: ...

    @abstractmethod
    async def is_syncing(self) -> bool: ...

    @abstractmethod
    async def close(self) -> None: ...
