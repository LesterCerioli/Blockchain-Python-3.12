
import json

import pytest

from app.services.defi.domain.exceptions import (
    DeFiError,
    IndexerLagError,
    InvalidAddressError,
    MarketDataError,
    NonCustodialViolationError,
    PoolNotFoundError,
    PositionNotFoundError,
    ProviderUnavailableError,
    RateLimitError,
    SanctionedAddressError,
    ToUNotAcceptedError,
    WalletConnectionError,
)

class TestHierarchy:
    def test_market_data_error_is_defi_error(self):
        assert issubclass(MarketDataError, DeFiError)

    def test_provider_unavailable_is_market_data(self):
        assert issubclass(ProviderUnavailableError, MarketDataError)

    def test_rate_limit_is_market_data(self):
        assert issubclass(RateLimitError, MarketDataError)

    def test_wallet_connection_is_defi_error(self):
        assert issubclass(WalletConnectionError, DeFiError)

    def test_invalid_address_is_wallet_connection(self):
        assert issubclass(InvalidAddressError, WalletConnectionError)

    def test_non_custodial_violation_is_defi_error(self):
        assert issubclass(NonCustodialViolationError, DeFiError)

    def test_sanctioned_address_is_defi_error(self):
        assert issubclass(SanctionedAddressError, DeFiError)

    def test_tou_not_accepted_is_defi_error(self):
        assert issubclass(ToUNotAcceptedError, DeFiError)

    def test_indexer_lag_is_defi_error(self):
        assert issubclass(IndexerLagError, DeFiError)


class TestNonCustodialViolationError:
    def test_violation_type_field(self):
        e = NonCustodialViolationError("PRIVATE_KEY_EXPOSURE")
        assert e.violation_type == "PRIVATE_KEY_EXPOSURE"

    def test_detail_optional(self):
        e = NonCustodialViolationError("SEED_PHRASE_REQUEST", "seed requested via API")
        assert e.detail == "seed requested via API"

    def test_message_contains_violation_type(self):
        e = NonCustodialViolationError("CUSTODY_TRANSFER")
        assert "CUSTODY_TRANSFER" in str(e)

    def test_to_dict_includes_violation_type(self):
        e = NonCustodialViolationError("PRIVATE_KEY_EXPOSURE", "details")
        d = e.to_dict()
        assert d["violation_type"] == "PRIVATE_KEY_EXPOSURE"
        assert d["detail"] == "details"


class TestToDict:
    def _assert_json_serializable(self, exc: DeFiError) -> None:
        d = exc.to_dict()
        dumped = json.dumps(d)
        assert isinstance(dumped, str)

    def test_base_to_dict_has_error_and_message(self):
        e = DeFiError("base error")
        d = e.to_dict()
        assert d["error"] == "DeFiError"
        assert d["message"] == "base error"

    def test_provider_unavailable_to_dict(self):
        e = ProviderUnavailableError("coingecko")
        d = e.to_dict()
        assert d["error"] == "ProviderUnavailableError"
        assert d["provider"] == "coingecko"
        self._assert_json_serializable(e)

    def test_rate_limit_to_dict_with_retry(self):
        e = RateLimitError("binance", retry_after=60)
        d = e.to_dict()
        assert d["retry_after"] == 60
        assert d["provider"] == "binance"
        self._assert_json_serializable(e)

    def test_rate_limit_to_dict_without_retry(self):
        e = RateLimitError("uniswap")
        d = e.to_dict()
        assert d["retry_after"] is None
        self._assert_json_serializable(e)

    def test_invalid_address_to_dict(self):
        e = InvalidAddressError("0xBAD")
        d = e.to_dict()
        assert d["address"] == "0xBAD"
        self._assert_json_serializable(e)

    def test_sanctioned_address_to_dict(self):
        e = SanctionedAddressError("0xDEAD")
        d = e.to_dict()
        assert d["address"] == "0xDEAD"
        self._assert_json_serializable(e)

    def test_tou_not_accepted_with_user_to_dict(self):
        e = ToUNotAcceptedError("user-42")
        d = e.to_dict()
        assert d["user_id"] == "user-42"
        self._assert_json_serializable(e)

    def test_tou_not_accepted_anonymous_to_dict(self):
        e = ToUNotAcceptedError()
        d = e.to_dict()
        assert d["user_id"] == ""
        self._assert_json_serializable(e)

    def test_indexer_lag_to_dict(self):
        e = IndexerLagError(12.75)
        d = e.to_dict()
        assert d["lag_seconds"] == 12.75
        self._assert_json_serializable(e)

    def test_pool_not_found_to_dict(self):
        e = PoolNotFoundError("0xPOOL")
        d = e.to_dict()
        assert d["address"] == "0xPOOL"
        self._assert_json_serializable(e)

    def test_position_not_found_to_dict(self):
        e = PositionNotFoundError("pos-99")
        d = e.to_dict()
        assert d["position_id"] == "pos-99"
        self._assert_json_serializable(e)
