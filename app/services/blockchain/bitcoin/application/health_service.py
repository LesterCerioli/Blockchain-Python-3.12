import asyncio
import time
from datetime import datetime, timezone
from typing import Optional

from ..domain.entities.node import NodeRecord, NodeStatus
from ..domain.interfaces.health_monitor import IHealthMonitor, NodeHealth
from ..domain.interfaces.node_adapter import IBitcoinNodeAdapter
from ..domain.interfaces.node_repository import INodeRepository
from ..infrastructure.providers.base_provider import BaseProvider


class HealthService(IHealthMonitor):

    def __init__(
        self,
        node_adapter: IBitcoinNodeAdapter,
        providers: list[BaseProvider],
        repository: INodeRepository,
        stale_block_threshold_seconds: int = 120,
    ) -> None:
        self._node_adapter = node_adapter
        self._providers = providers
        self._repository = repository
        self._stale_threshold = stale_block_threshold_seconds

    async def check_health(self) -> list[NodeHealth]:
        tasks = [self._check_one(provider) for provider in self._providers]
        return await asyncio.gather(*tasks)

    async def get_current_block_height(self) -> Optional[int]:
        try:
            return await self._node_adapter.get_block_height()
        except Exception:
            return None

    async def _check_one(self, provider: BaseProvider) -> NodeHealth:
        start = time.monotonic()
        try:
            block = await provider.get_block_height()
            latency_ms = (time.monotonic() - start) * 1000
            is_stale = await self._is_stale(provider.name, block)
            status = NodeStatus.DEGRADED if is_stale else NodeStatus.HEALTHY

            await self._safe_upsert(
                NodeRecord(
                    name=provider.name,
                    url=provider.url,
                    priority=provider.priority,
                    status=status,
                    last_seen_block=block,
                    last_checked_at=datetime.now(tz=timezone.utc),
                )
            )
            return NodeHealth(
                node_name=provider.name,
                is_healthy=True,
                block_height=block,
                latency_ms=round(latency_ms, 2),
                last_error=None,
                is_stale=is_stale,
            )
        except Exception as exc:
            latency_ms = (time.monotonic() - start) * 1000
            await self._safe_upsert(
                NodeRecord(
                    name=provider.name,
                    url=provider.url,
                    priority=provider.priority,
                    status=NodeStatus.DOWN,
                    last_seen_block=None,
                    last_checked_at=datetime.now(tz=timezone.utc),
                )
            )
            return NodeHealth(
                node_name=provider.name,
                is_healthy=False,
                block_height=None,
                latency_ms=round(latency_ms, 2),
                last_error=str(exc),
                is_stale=False,
            )

    async def _is_stale(self, node_name: str, current_block: int) -> bool:
        try:
            record = await self._repository.get_by_name(node_name)
        except Exception:
            return False
        if record is None or record.last_seen_block is None or record.last_checked_at is None:
            return False
        elapsed = (
            datetime.now(tz=timezone.utc) - record.last_checked_at
        ).total_seconds()
        return elapsed > self._stale_threshold and record.last_seen_block == current_block

    async def _safe_upsert(self, record: NodeRecord) -> None:
        try:
            await self._repository.upsert(record)
        except Exception:
            pass
