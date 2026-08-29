import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ProviderStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class ProviderRecord:
    name: str
    url: str
    priority: int
    status: ProviderStatus = ProviderStatus.UNKNOWN
    last_seen_block: int | None = None
    last_checked_at: datetime | None = None
    id: uuid.UUID | None = None
