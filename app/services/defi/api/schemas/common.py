from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, model_validator

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated wrapper for list endpoints.

    ``pages``, ``has_next`` and ``has_previous`` are computed automatically
    from ``total``, ``page`` and ``page_size`` — callers must not supply them.
    """

    items: list[T]
    total: int = Field(ge=0, description="Total number of items matching the query")
    page: int = Field(ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(ge=1, le=500, description="Maximum items returned per page")
    pages: int = Field(default=0, ge=0, description="Total number of pages")
    has_next: bool = Field(default=False, description="Whether a next page exists")
    has_previous: bool = Field(default=False, description="Whether a previous page exists")

    @model_validator(mode="after")
    def _derive_pagination_fields(self) -> "PaginatedResponse[T]":
        self.pages = math.ceil(self.total / self.page_size) if self.total > 0 else 0
        self.has_next = self.page < self.pages
        self.has_previous = self.page > 1
        return self

    @classmethod
    def of(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Convenience factory — preferred over direct construction."""
        return cls(items=items, total=total, page=page, page_size=page_size)

    model_config = {"populate_by_name": True}


class ErrorResponse(BaseModel):
    """Structured error envelope returned by all DeFi exception handlers.

    ``request_id`` ties every error to a traceable unit for audit logs.
    ``error_code`` is machine-readable; ``message`` is human-readable.
    ``details`` carries domain-specific fields (e.g. ``address``, ``provider``)
    stripped of any sensitive internals.
    """

    error_code: str = Field(description="Machine-readable error identifier")
    message: str = Field(description="Human-readable error description")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Domain-specific extra context (no sensitive data)",
    )
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID v4 correlating this error to an audit log entry",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="UTC timestamp of when the error occurred (ISO 8601)",
    )
    path: str | None = Field(
        default=None,
        description="Request path that produced this error",
    )

    model_config = {"populate_by_name": True}


class HealthStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


class HealthResponse(BaseModel):
    """Service health envelope used by every /health endpoint.

    ``checks`` maps component names (e.g. ``"chain_rpc"``, ``"price_feed"``)
    to their individual status strings so operators can pinpoint degradation.
    """

    status: HealthStatus = Field(description="Overall service health status")
    version: str | None = Field(
        default=None,
        description="Running service version (semver)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="UTC timestamp of this health check (ISO 8601)",
    )
    checks: dict[str, str] | None = Field(
        default=None,
        description="Per-component health status map",
    )

    model_config = {"populate_by_name": True}
