from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional


class CircuitState(str, Enum):
    CLOSED = "closed"       # normal operation
    OPEN = "open"           # rejecting all requests
    HALF_OPEN = "half_open" # probing for recovery


class CircuitBreaker:
    """
    Classic three-state circuit breaker (SRP: only manages state transitions).
    Thread-safe for single-event-loop use.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
    ) -> None:
        self.name = name
        self._failure_threshold = failure_threshold
        self._recovery_timeout = timedelta(seconds=recovery_timeout_seconds)
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None

    @property
    def state(self) -> CircuitState:
        # Lazily transition OPEN → HALF_OPEN when the timeout has elapsed
        if (
            self._state == CircuitState.OPEN
            and self._last_failure_time is not None
            and datetime.now(tz=timezone.utc) > self._last_failure_time + self._recovery_timeout
        ):
            self._state = CircuitState.HALF_OPEN
        return self._state

    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = datetime.now(tz=timezone.utc)
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN
