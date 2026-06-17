from abc import ABC, abstractmethod
from typing import Any, Optional


class IQuoteCache(ABC):

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]: ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> None: ...

    @abstractmethod
    async def get_many(self, keys: list[str]) -> list[Optional[Any]]: ...

    @abstractmethod
    async def set_many(self, items: dict[str, Any], ttl: int) -> None: ...
