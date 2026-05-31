import sys
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from services.blockchain.ethereum.application.health_service import HealthService
from services.blockchain.ethereum.domain.entities.provider import ProviderRecord, ProviderStatus
from services.blockchain.ethereum.infrastructure.persistence.in_memory_provider_repository import (
    InMemoryProviderRepository,
)


def _make_provider(name: str, block_number: int | None = 20_000_000, priority: int = 1):
    provider = MagicMock()
    provider.name = name
    provider.url = f"http://{name}.local"
    provider.priority = priority
    if block_number is not None:
        provider.get_block_number = AsyncMock(return_value=block_number)
    else:
        provider.get_block_number = AsyncMock(side_effect=ConnectionError("node down"))
    return provider


def _make_chain_adapter(block_number: int | None = 20_000_000):
    adapter = MagicMock()
    if block_number is not None:
        adapter.get_block_number = AsyncMock(return_value=block_number)
    else:
        adapter.get_block_number = AsyncMock(side_effect=RuntimeError("all providers down"))
    return adapter


@pytest.mark.asyncio
async def test_healthy_provider_returns_healthy_status():
    provider = _make_provider("primary", block_number=20_000_000)
    repo = InMemoryProviderRepository()
    service = HealthService(
        chain_adapter=_make_chain_adapter(),
        providers=[provider],
        repository=repo,
    )

    results = await service.check_health()

    assert len(results) == 1
    assert results[0].is_healthy is True
    assert results[0].block_height == 20_000_000
    assert results[0].last_error is None


@pytest.mark.asyncio
async def test_failing_provider_returns_unhealthy_status():
    provider = _make_provider("primary", block_number=None)
    repo = InMemoryProviderRepository()
    service = HealthService(
        chain_adapter=_make_chain_adapter(block_number=None),
        providers=[provider],
        repository=repo,
    )

    results = await service.check_health()

    assert results[0].is_healthy is False
    assert results[0].block_height is None
    assert results[0].last_error is not None


@pytest.mark.asyncio
async def test_stale_block_detected():
    repo = InMemoryProviderRepository()
    stale_time = datetime.now(tz=timezone.utc) - timedelta(seconds=120)
    await repo.upsert(
        ProviderRecord(
            name="primary",
            url="http://primary.local",
            priority=1,
            status=ProviderStatus.HEALTHY,
            last_seen_block=20_000_000,
            last_checked_at=stale_time,
        )
    )
    provider = _make_provider("primary", block_number=20_000_000)
    service = HealthService(
        chain_adapter=_make_chain_adapter(),
        providers=[provider],
        repository=repo,
        stale_block_threshold_seconds=60,
    )

    results = await service.check_health()

    assert results[0].is_healthy is True
    assert results[0].is_stale is True


@pytest.mark.asyncio
async def test_get_current_block_height_returns_value():
    adapter = _make_chain_adapter(block_number=99_999)
    service = HealthService(
        chain_adapter=adapter,
        providers=[],
        repository=InMemoryProviderRepository(),
    )
    height = await service.get_current_block_height()
    assert height == 99_999


@pytest.mark.asyncio
async def test_get_current_block_height_returns_none_on_error():
    adapter = _make_chain_adapter(block_number=None)
    service = HealthService(
        chain_adapter=adapter,
        providers=[],
        repository=InMemoryProviderRepository(),
    )
    height = await service.get_current_block_height()
    assert height is None


@pytest.mark.asyncio
async def test_db_failure_does_not_affect_health_result():
    provider = _make_provider("primary", block_number=20_000_000)

    repo = MagicMock()
    repo.get_by_name = AsyncMock(side_effect=RuntimeError("DB down"))
    repo.upsert = AsyncMock(side_effect=RuntimeError("DB down"))

    service = HealthService(
        chain_adapter=_make_chain_adapter(),
        providers=[provider],
        repository=repo,
    )

    results = await service.check_health()
    assert results[0].is_healthy is True


@pytest.mark.asyncio
async def test_multiple_providers_checked_in_parallel():
    p1 = _make_provider("primary", block_number=20_000_000, priority=1)
    p2 = _make_provider("secondary", block_number=19_999_990, priority=2)
    repo = InMemoryProviderRepository()
    service = HealthService(
        chain_adapter=_make_chain_adapter(),
        providers=[p1, p2],
        repository=repo,
    )

    results = await service.check_health()

    assert len(results) == 2
    names = {r.provider_name for r in results}
    assert names == {"primary", "secondary"}
