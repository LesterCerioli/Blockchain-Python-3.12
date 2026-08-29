from unittest.mock import AsyncMock, patch

import pytest

from app.services.defi.domain.exceptions import RateLimitError
from app.services.defi.infrastructure.market_data.rate_limiter import RedisRateLimiter

_PROVIDER = "TestProvider"
_MAX_REQUESTS = 5


def _make_redis(incr_return: int) -> AsyncMock:
    redis = AsyncMock()
    redis.incr.return_value = incr_return
    redis.expire = AsyncMock()
    return redis


@pytest.mark.asyncio
async def test_first_request_sets_expiry() -> None:
    redis = _make_redis(incr_return=1)
    limiter = RedisRateLimiter(redis, _PROVIDER, _MAX_REQUESTS)

    await limiter.check_and_increment()

    redis.incr.assert_called_once()
    redis.expire.assert_called_once()
    key = redis.incr.call_args[0][0]
    assert key.startswith(f"defi:rate_limit:{_PROVIDER}:")


@pytest.mark.asyncio
async def test_subsequent_request_skips_expire() -> None:
    redis = _make_redis(incr_return=2)
    limiter = RedisRateLimiter(redis, _PROVIDER, _MAX_REQUESTS)

    await limiter.check_and_increment()

    redis.expire.assert_not_called()


@pytest.mark.asyncio
async def test_within_limit_does_not_raise() -> None:
    redis = _make_redis(incr_return=_MAX_REQUESTS)
    limiter = RedisRateLimiter(redis, _PROVIDER, _MAX_REQUESTS)

    await limiter.check_and_increment()  # should not raise


@pytest.mark.asyncio
async def test_exceeding_limit_raises_rate_limit_error() -> None:
    redis = _make_redis(incr_return=_MAX_REQUESTS + 1)
    limiter = RedisRateLimiter(redis, _PROVIDER, _MAX_REQUESTS)

    with pytest.raises(RateLimitError) as exc_info:
        await limiter.check_and_increment()

    assert exc_info.value.provider == _PROVIDER


@pytest.mark.asyncio
async def test_key_uses_60s_window() -> None:
    redis = _make_redis(incr_return=1)
    limiter = RedisRateLimiter(redis, _PROVIDER, _MAX_REQUESTS)

    fixed_time = 1_700_000_070.5
    with patch("app.services.defi.infrastructure.market_data.rate_limiter.time") as mock_time:
        mock_time.time.return_value = fixed_time
        await limiter.check_and_increment()

    expected_window = int(fixed_time) // 60
    expected_key = f"defi:rate_limit:{_PROVIDER}:{expected_window}"
    redis.incr.assert_called_once_with(expected_key)
    redis.expire.assert_called_once_with(expected_key, 60)
