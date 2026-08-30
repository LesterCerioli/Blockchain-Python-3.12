import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class NodeStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class NodeRecord:
    name: str
    url: str
    priority: int
    status: NodeStatus = NodeStatus.UNKNOWN
    last_seen_block: Optional[int] = None
    last_checked_at: Optional[datetime] = None
    id: Optional[uuid.UUID] = None
