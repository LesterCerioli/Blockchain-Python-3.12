import asyncio
import time
from datetime import datetime, timezone
from typing import Optional

from ..domain.entities.provider import ProviderRecord, ProviderStatus
from ..domain.interfaces.chain_adapter import IChainAdapter
from ..domain.interfaces.health_monitor import IHealthMonitor, ProviderHealth
from ..domain.interfaces.provider_repository import IProviderRepository
from ..infrastructure.providers.base_provider import BaseProvider


class HealthService(IHealthMonitor):
    """
    Application service that checks each provider in parallel, updates the
    repository, and detects stale blocks (SRP: only orchestrates health checks).
    Depends on abstractions (IChainAdapter, IProviderRepository) not concretes.
    """

    def __init__(
        self,
        chain_adapter: IChainAdapter,
        providers: list[BaseProvider],
        repository: IProviderRepository,
        stale_block_threshold_seconds: int = 60,
    ) -> None:
        self._chain_adapter = chain_adapter
        self._providers = providers
        self._repository = repository
        self._stale_threshold = stale_block_threshold_seconds

    async def check_health(self) -> list[ProviderHealth]:
        tasks = [self._check_one(provider) for provider in self._providers]
        return await asyncio.gather(*tasks)

    async def get_current_block_height(self) -> Optional[int]:
        try:
            return await self._chain_adapter.get_block_number()
        except Exception:
            return None

    async def _check_one(self, provider: BaseProvider) -> ProviderHealth:
        start = time.monotonic()
        try:
            block = await provider.get_block_number()
            latency_ms = (time.monotonic() - start) * 1000
            is_stale = await self._is_stale(provider.name, block)
            status = ProviderStatus.DEGRADED if is_stale else ProviderStatus.HEALTHY

            await self._safe_upsert(
                ProviderRecord(
                    name=provider.name,
                    url=provider.url,
                    priority=provider.priority,
                    status=status,
                    last_seen_block=block,
                    last_checked_at=datetime.now(tz=timezone.utc),
                )
            )
            return ProviderHealth(
                provider_name=provider.name,
                is_healthy=True,
                block_height=block,
                latency_ms=round(latency_ms, 2),
                last_error=None,
                is_stale=is_stale,
            )
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            await self._safe_upsert(
                ProviderRecord(
                    name=provider.name,
                    url=provider.url,
                    priority=provider.priority,
                    status=ProviderStatus.DOWN,
                    last_seen_block=None,
                    last_checked_at=datetime.now(tz=timezone.utc),
                )
            )
            return ProviderHealth(
                provider_name=provider.name,
                is_healthy=False,
                block_height=None,
                latency_ms=round(latency_ms, 2),
                last_error=str(exc),
                is_stale=False,
            )

    async def _is_stale(self, provider_name: str, current_block: int) -> bool:
        try:
            record = await self._repository.get_by_name(provider_name)
        except Exception:
            return False
        if record is None or record.last_seen_block is None or record.last_checked_at is None:
            return False
        elapsed = (
            datetime.now(tz=timezone.utc) - record.last_checked_at
        ).total_seconds()
        return elapsed > self._stale_threshold and record.last_seen_block == current_block

    async def _safe_upsert(self, record: ProviderRecord) -> None:
        try:
            await self._repository.upsert(record)
        except Exception:
            # DB failure must not propagate into health check response
            pass
