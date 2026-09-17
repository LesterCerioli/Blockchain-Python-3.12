from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any

from ..entities.blockchain_event import BlockchainEvent

EventHandler = Callable[[BlockchainEvent], Coroutine[Any, Any, None]]


class IEventBus(ABC):

    @abstractmethod
    async def publish(self, event: BlockchainEvent) -> None: ...

    @abstractmethod
    async def subscribe(self, event_type: str, handler: EventHandler) -> str:
        """Registers a handler for a given event type and returns a subscription ID."""
        ...

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None: ...

    @abstractmethod
    async def get_pending_events(
        self,
        event_type: str,
        limit: int = 100,
    ) -> list[BlockchainEvent]:
        """Returns unprocessed events of a given type, oldest first."""
        ...
