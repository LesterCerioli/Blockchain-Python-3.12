from __future__ import annotations

import time

from redis.asyncio import Redis

from ...domain.exceptions import RateLimitError

_WINDOW_SECONDS = 60


class RedisRateLimiter:
    
    def __init__(self, redis: Redis, provider: str, max_requests: int) -> None:
        self._redis = redis
        self._provider = provider
        self._max_requests = max_requests

    def _current_key(self) -> str:
        window = int(time.time()) // _WINDOW_SECONDS
        return f"defi:rate_limit:{self._provider}:{window}"

    async def check_and_increment(self) -> None:
        key = self._current_key()
        count = await self._redis.incr(key)
        if count == 1:
            await self._redis.expire(key, _WINDOW_SECONDS)
        if count > self._max_requests:
            raise RateLimitError(self._provider)
