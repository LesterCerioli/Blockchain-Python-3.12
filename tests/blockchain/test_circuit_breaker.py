import sys
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from services.blockchain.ethereum.infrastructure.rpc.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
)


def test_starts_closed():
    cb = CircuitBreaker("test")
    assert cb.state == CircuitState.CLOSED
    assert not cb.is_open()


def test_opens_after_threshold():
    cb = CircuitBreaker("test", failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.is_open()


def test_success_resets_to_closed():
    cb = CircuitBreaker("test", failure_threshold=2)
    cb.record_failure()
    cb.record_failure()
    assert cb.is_open()
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert not cb.is_open()


def test_transitions_to_half_open_after_timeout():
    cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout_seconds=60)
    cb.record_failure()
    assert cb.is_open()

    past = datetime.now(tz=timezone.utc) - timedelta(seconds=61)
    cb._last_failure_time = past

    # Next state read should transition to HALF_OPEN
    assert cb.state == CircuitState.HALF_OPEN
    assert not cb.is_open()
