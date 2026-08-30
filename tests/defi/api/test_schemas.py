"""Serialization tests for shared DeFi response schemas (FEATURE 1.2.2).

Covers PaginatedResponse[T], ErrorResponse, and HealthResponse, verifying:
- correct field computation / defaults
- round-trip JSON serialisation (model → dict → JSON → model)
- schema constraints (ge/le validators)
- generic type parameter acceptance
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.services.defi.api.schemas.common import (
    ErrorResponse,
    HealthResponse,
    HealthStatus,
    PaginatedResponse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_round_trip(model) -> dict:
    """Serialise a model to JSON and parse it back into a plain dict."""
    raw = json.dumps(model.model_dump(mode="json"))
    return json.loads(raw)


# ---------------------------------------------------------------------------
# PaginatedResponse
# ---------------------------------------------------------------------------

class TestPaginatedResponse:
    def test_generic_with_str_items(self):
        resp: PaginatedResponse[str] = PaginatedResponse.of(
            items=["a", "b", "c"], total=3, page=1, page_size=10
        )
        assert resp.items == ["a", "b", "c"]

    def test_generic_with_dict_items(self):
        items = [{"address": "0xABC", "symbol": "ETH"}]
        resp: PaginatedResponse[dict] = PaginatedResponse.of(
            items=items, total=1, page=1, page_size=10
        )
        assert resp.items[0]["symbol"] == "ETH"

    def test_pages_computed_exactly(self):
        resp = PaginatedResponse.of(items=[], total=25, page=1, page_size=10)
        assert resp.pages == 3

    def test_pages_computed_no_remainder(self):
        resp = PaginatedResponse.of(items=[], total=20, page=1, page_size=10)
        assert resp.pages == 2

    def test_pages_zero_when_total_zero(self):
        resp = PaginatedResponse.of(items=[], total=0, page=1, page_size=10)
        assert resp.pages == 0

    def test_has_next_true(self):
        resp = PaginatedResponse.of(items=[], total=30, page=1, page_size=10)
        assert resp.has_next is True

    def test_has_next_false_on_last_page(self):
        resp = PaginatedResponse.of(items=[], total=30, page=3, page_size=10)
        assert resp.has_next is False

    def test_has_previous_false_on_first_page(self):
        resp = PaginatedResponse.of(items=[], total=30, page=1, page_size=10)
        assert resp.has_previous is False

    def test_has_previous_true_on_second_page(self):
        resp = PaginatedResponse.of(items=[], total=30, page=2, page_size=10)
        assert resp.has_previous is True

    def test_single_page_no_next_no_previous(self):
        resp = PaginatedResponse.of(items=["x"], total=1, page=1, page_size=10)
        assert resp.has_next is False
        assert resp.has_previous is False
        assert resp.pages == 1

    def test_json_serializable(self):
        resp = PaginatedResponse.of(items=[1, 2], total=2, page=1, page_size=10)
        data = _json_round_trip(resp)
        assert data["total"] == 2
        assert data["pages"] == 1
        assert data["has_next"] is False
        assert data["has_previous"] is False
        assert data["items"] == [1, 2]

    def test_page_size_upper_bound(self):
        with pytest.raises(ValidationError):
            PaginatedResponse.of(items=[], total=0, page=1, page_size=501)

    def test_page_lower_bound(self):
        with pytest.raises(ValidationError):
            PaginatedResponse.of(items=[], total=0, page=0, page_size=10)

    def test_total_cannot_be_negative(self):
        with pytest.raises(ValidationError):
            PaginatedResponse.of(items=[], total=-1, page=1, page_size=10)


# ---------------------------------------------------------------------------
# ErrorResponse
# ---------------------------------------------------------------------------

class TestErrorResponse:
    def test_minimal_construction(self):
        err = ErrorResponse(error_code="TOKEN_NOT_FOUND", message="Token not found")
        assert err.error_code == "TOKEN_NOT_FOUND"
        assert err.message == "Token not found"
        assert err.details is None
        assert err.path is None

    def test_request_id_auto_generated_as_uuid(self):
        err = ErrorResponse(error_code="E", message="m")
        parsed = uuid.UUID(err.request_id)
        assert parsed.version == 4

    def test_request_id_is_unique_per_instance(self):
        e1 = ErrorResponse(error_code="E", message="m")
        e2 = ErrorResponse(error_code="E", message="m")
        assert e1.request_id != e2.request_id

    def test_custom_request_id_preserved(self):
        rid = "my-trace-id-123"
        err = ErrorResponse(error_code="E", message="m", request_id=rid)
        assert err.request_id == rid

    def test_timestamp_is_utc(self):
        err = ErrorResponse(error_code="E", message="m")
        assert err.timestamp.tzinfo is not None
        assert err.timestamp.tzinfo == timezone.utc

    def test_details_accepted(self):
        err = ErrorResponse(
            error_code="INVALID_ADDRESS",
            message="Bad address",
            details={"address": "0xBAD"},
        )
        assert err.details["address"] == "0xBAD"

    def test_path_accepted(self):
        err = ErrorResponse(error_code="E", message="m", path="/api/v1/defi/quotes")
        assert err.path == "/api/v1/defi/quotes"

    def test_json_serializable_with_datetime(self):
        err = ErrorResponse(
            error_code="RATE_LIMIT_EXCEEDED",
            message="Rate limit hit",
            details={"provider": "coingecko"},
            path="/api/v1/defi/quotes",
        )
        data = _json_round_trip(err)
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert data["details"]["provider"] == "coingecko"
        assert isinstance(data["timestamp"], str)
        assert data["request_id"] is not None

    def test_all_defi_error_codes_are_strings(self):
        codes = [
            "INVALID_ADDRESS", "SANCTIONED_ADDRESS", "TOU_NOT_ACCEPTED",
            "NON_CUSTODIAL_VIOLATION", "TOKEN_NOT_FOUND", "POOL_NOT_FOUND",
            "NO_POOLS_FOR_PAIR", "POSITION_NOT_FOUND", "PRICE_UNAVAILABLE",
            "SLIPPAGE_EXCEEDED", "INSUFFICIENT_LIQUIDITY", "PROTOCOL_NOT_SUPPORTED",
            "RATE_LIMIT_EXCEEDED", "PROVIDER_UNAVAILABLE", "INDEXER_LAG",
            "MARKET_DATA_ERROR", "WALLET_CONNECTION_ERROR", "INTERNAL_DEFI_ERROR",
        ]
        for code in codes:
            err = ErrorResponse(error_code=code, message="test")
            assert err.error_code == code


# ---------------------------------------------------------------------------
# HealthResponse
# ---------------------------------------------------------------------------

class TestHealthResponse:
    def test_status_ok(self):
        resp = HealthResponse(status=HealthStatus.OK)
        assert resp.status == HealthStatus.OK

    def test_status_degraded(self):
        resp = HealthResponse(status=HealthStatus.DEGRADED)
        assert resp.status == HealthStatus.DEGRADED

    def test_status_down(self):
        resp = HealthResponse(status=HealthStatus.DOWN)
        assert resp.status == HealthStatus.DOWN

    def test_status_from_string_ok(self):
        resp = HealthResponse(status="ok")  # type: ignore[arg-type]
        assert resp.status == HealthStatus.OK

    def test_status_from_string_degraded(self):
        resp = HealthResponse(status="degraded")  # type: ignore[arg-type]
        assert resp.status == HealthStatus.DEGRADED

    def test_status_from_string_down(self):
        resp = HealthResponse(status="down")  # type: ignore[arg-type]
        assert resp.status == HealthStatus.DOWN

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            HealthResponse(status="unknown")  # type: ignore[arg-type]

    def test_timestamp_defaults_to_utc(self):
        resp = HealthResponse(status=HealthStatus.OK)
        assert resp.timestamp.tzinfo == timezone.utc

    def test_version_optional(self):
        resp = HealthResponse(status=HealthStatus.OK)
        assert resp.version is None

    def test_version_accepted(self):
        resp = HealthResponse(status=HealthStatus.OK, version="1.2.2")
        assert resp.version == "1.2.2"

    def test_checks_optional(self):
        resp = HealthResponse(status=HealthStatus.OK)
        assert resp.checks is None

    def test_checks_accepted(self):
        resp = HealthResponse(
            status=HealthStatus.DEGRADED,
            checks={"chain_rpc": "ok", "price_feed": "degraded"},
        )
        assert resp.checks["price_feed"] == "degraded"

    def test_json_serializable(self):
        resp = HealthResponse(
            status=HealthStatus.OK,
            version="1.2.2",
            checks={"chain_rpc": "ok"},
        )
        data = _json_round_trip(resp)
        assert data["status"] == "ok"
        assert data["version"] == "1.2.2"
        assert isinstance(data["timestamp"], str)
        assert data["checks"]["chain_rpc"] == "ok"

    def test_json_status_values_are_lowercase_strings(self):
        for status, expected in [
            (HealthStatus.OK, "ok"),
            (HealthStatus.DEGRADED, "degraded"),
            (HealthStatus.DOWN, "down"),
        ]:
            data = _json_round_trip(HealthResponse(status=status))
            assert data["status"] == expected
