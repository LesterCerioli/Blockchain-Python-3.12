import json
import os
from datetime import datetime, timedelta

import redis
from redis.asyncio import Redis

REDIS_URL = os.getenv("CACHE_URL", "redis://localhost:6379/1")

__all__ = ["get", "set"]


_redis_client: Redis | None = None


def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


async def get(key: str) -> Optional[Any]:
    try:
        r = get_redis()
        value = r.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    except (redis.ConnectionError, redis.TimeoutError):
        return None


async def set(key: str, value: Any, ttl: int = 300) -> None:
    try:
        r = get_redis()
        serialized = json.dumps(value, default=str)
        r.setex(key, ttl, serialized)
    except (redis.ConnectionError, redis.TimeoutError):
        pass