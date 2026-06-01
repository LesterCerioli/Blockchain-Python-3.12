"""Unit tests for FEATURE 1.1.3 — Immutable value objects (issue #42).

Covers: TokenAddress, ChainId, FiatPrice, CryptoAmount, TxHash.
DoD:
- All value objects are frozen (FrozenInstanceError on mutation).
- TokenAddress rejects invalid addresses.
- ChainId rejects unsupported chains.
- Invalid cases are fully covered.
"""
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.services.defi.domain.value_objects import (
    ChainId,
    CryptoAmount,
    FiatPrice,
    TokenAddress,
    TxHash,
)
from app.services.defi.domain.value_objects.chain_id import SUPPORTED_CHAIN_IDS

# ---------------------------------------------------------------------------
# TokenAddress
# ---------------------------------------------------------------------------

VALID_ADDRESS_LOWER = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
VALID_ADDRESS_CHECKSUM = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
VALID_ADDRESS_UPPER = "0xA0B86991C6218B36C1D19D4A2E9EB0CE3606EB48"


class TestTokenAddress:
    def test_accepts_lowercase_address(self):
        token = TokenAddress(VALID_ADDRESS_LOWER)
        assert token.value == VALID_ADDRESS_CHECKSUM

    def test_accepts_checksummed_address(self):
        token = TokenAddress(VALID_ADDRESS_CHECKSUM)
        assert token.value == VALID_ADDRESS_CHECKSUM

    def test_accepts_uppercase_address_and_normalizes(self):
        token = TokenAddress(VALID_ADDRESS_UPPER)
        assert token.value == VALID_ADDRESS_CHECKSUM

    def test_str_returns_checksummed_value(self):
        token = TokenAddress(VALID_ADDRESS_LOWER)
        assert str(token) == VALID_ADDRESS_CHECKSUM

    def test_equality_regardless_of_input_case(self):
        a = TokenAddress(VALID_ADDRESS_LOWER)
        b = TokenAddress(VALID_ADDRESS_CHECKSUM)
        assert a == b

    def test_hash_consistent_across_instances(self):
        a = TokenAddress(VALID_ADDRESS_LOWER)
        b = TokenAddress(VALID_ADDRESS_CHECKSUM)
        assert hash(a) == hash(b)

    def test_frozen_raises_on_mutation(self):
        token = TokenAddress(VALID_ADDRESS_LOWER)
        with pytest.raises(FrozenInstanceError):
            token.value = "0x" + "0" * 40  # type: ignore[misc]

    def test_rejects_too_short_address(self):
        with pytest.raises(ValueError):
            TokenAddress("0x1234")

    def test_rejects_address_without_0x_prefix(self):
        with pytest.raises(ValueError):
            TokenAddress("a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError):
            TokenAddress("")

    def test_rejects_random_string(self):
        with pytest.raises(ValueError):
            TokenAddress("not-an-address")

    def test_rejects_address_wrong_length_too_long(self):
        with pytest.raises(ValueError):
            TokenAddress("0x" + "a" * 41)

    def test_rejects_non_hex_characters(self):
        with pytest.raises(ValueError):
            TokenAddress("0x" + "z" * 40)


# ---------------------------------------------------------------------------
# ChainId
# ---------------------------------------------------------------------------

class TestChainId:
    @pytest.mark.parametrize("chain_id", sorted(SUPPORTED_CHAIN_IDS))
    def test_accepts_all_supported_chains(self, chain_id: int):
        c = ChainId(chain_id)
        assert c.value == chain_id

    def test_ethereum_mainnet(self):
        c = ChainId(1)
        assert c.value == 1

    def test_polygon(self):
        c = ChainId(137)
        assert c.value == 137

    def test_arbitrum_one(self):
        c = ChainId(42161)
        assert c.value == 42161

    def test_base(self):
        c = ChainId(8453)
        assert c.value == 8453

    def test_int_conversion(self):
        assert int(ChainId(1)) == 1

    def test_str_conversion(self):
        assert str(ChainId(137)) == "137"

    def test_frozen_raises_on_mutation(self):
        c = ChainId(1)
        with pytest.raises(FrozenInstanceError):
            c.value = 137  # type: ignore[misc]

    def test_rejects_bsc(self):
        with pytest.raises(ValueError, match="Unsupported chain_id"):
            ChainId(56)

    def test_rejects_avalanche(self):
        with pytest.raises(ValueError, match="Unsupported chain_id"):
            ChainId(43114)

    def test_rejects_zero(self):
        with pytest.raises(ValueError, match="Unsupported chain_id"):
            ChainId(0)

    def test_rejects_negative(self):
        with pytest.raises(ValueError, match="Unsupported chain_id"):
            ChainId(-1)

    def test_error_message_lists_supported_chains(self):
        with pytest.raises(ValueError, match="1") as exc_info:
            ChainId(999)
        assert "Supported chains" in str(exc_info.value)

    def test_equality(self):
        assert ChainId(1) == ChainId(1)
        assert ChainId(1) != ChainId(137)

    def test_hash(self):
        assert hash(ChainId(1)) == hash(ChainId(1))


# ---------------------------------------------------------------------------
# FiatPrice
# ---------------------------------------------------------------------------

class TestFiatPrice:
    def test_valid_usd(self):
        p = FiatPrice(amount=Decimal("3000.00"), currency="USD")
        assert p.amount == Decimal("3000.00")
        assert p.currency == "USD"

    def test_valid_eur(self):
        p = FiatPrice(amount=Decimal("1.50"), currency="EUR")
        assert p.currency == "EUR"

    def test_valid_brl(self):
        p = FiatPrice(amount=Decimal("0.01"), currency="BRL")
        assert p.currency == "BRL"

    def test_currency_normalized_to_uppercase(self):
        p = FiatPrice(amount=Decimal("100"), currency="usd")
        assert p.currency == "USD"

    def test_currency_normalized_strips_whitespace(self):
        p = FiatPrice(amount=Decimal("100"), currency=" EUR ")
        assert p.currency == "EUR"

    def test_zero_amount_is_valid(self):
        p = FiatPrice(amount=Decimal("0"), currency="USD")
        assert p.amount == Decimal("0")

    def test_str_representation(self):
        p = FiatPrice(amount=Decimal("3000"), currency="USD")
        assert str(p) == "3000 USD"

    def test_frozen_raises_on_mutation(self):
        p = FiatPrice(amount=Decimal("100"), currency="USD")
        with pytest.raises(FrozenInstanceError):
            p.amount = Decimal("200")  # type: ignore[misc]

    def test_rejects_negative_amount(self):
        with pytest.raises(ValueError, match="must be >= 0"):
            FiatPrice(amount=Decimal("-0.01"), currency="USD")

    def test_rejects_currency_too_short(self):
        with pytest.raises(ValueError, match="ISO 4217"):
            FiatPrice(amount=Decimal("1"), currency="US")

    def test_rejects_currency_too_long(self):
        with pytest.raises(ValueError, match="ISO 4217"):
            FiatPrice(amount=Decimal("1"), currency="USDT")

    def test_rejects_currency_with_digits(self):
        with pytest.raises(ValueError, match="ISO 4217"):
            FiatPrice(amount=Decimal("1"), currency="U5D")

    def test_rejects_empty_currency(self):
        with pytest.raises(ValueError, match="ISO 4217"):
            FiatPrice(amount=Decimal("1"), currency="")

    def test_equality(self):
        a = FiatPrice(amount=Decimal("100"), currency="USD")
        b = FiatPrice(amount=Decimal("100"), currency="usd")
        assert a == b


# ---------------------------------------------------------------------------
# CryptoAmount
# ---------------------------------------------------------------------------

class TestCryptoAmount:
    def test_valid_with_18_decimals(self):
        one_eth = 10 ** 18
        ca = CryptoAmount(raw=one_eth, decimals=18)
        assert ca.as_decimal == Decimal("1")

    def test_valid_with_6_decimals(self):
        one_usdc = 1_000_000
        ca = CryptoAmount(raw=one_usdc, decimals=6)
        assert ca.as_decimal == Decimal("1")

    def test_valid_zero(self):
        ca = CryptoAmount(raw=0, decimals=18)
        assert ca.as_decimal == Decimal("0")

    def test_valid_zero_decimals(self):
        ca = CryptoAmount(raw=5, decimals=0)
        assert ca.as_decimal == Decimal("5")

    def test_repr(self):
        ca = CryptoAmount(raw=10 ** 18, decimals=18)
        assert "1" in repr(ca)

    def test_frozen_raises_on_mutation(self):
        ca = CryptoAmount(raw=100, decimals=6)
        with pytest.raises(FrozenInstanceError):
            ca.raw = 200  # type: ignore[misc]

    def test_rejects_negative_raw(self):
        with pytest.raises(ValueError, match="must be >= 0"):
            CryptoAmount(raw=-1, decimals=18)

    def test_rejects_decimals_above_18(self):
        with pytest.raises(ValueError, match="must be in \\[0, 18\\]"):
            CryptoAmount(raw=1, decimals=19)

    def test_rejects_negative_decimals(self):
        with pytest.raises(ValueError, match="must be in \\[0, 18\\]"):
            CryptoAmount(raw=1, decimals=-1)

    def test_equality(self):
        a = CryptoAmount(raw=1000, decimals=6)
        b = CryptoAmount(raw=1000, decimals=6)
        assert a == b

    def test_inequality_different_raw(self):
        assert CryptoAmount(raw=1, decimals=6) != CryptoAmount(raw=2, decimals=6)

    def test_inequality_different_decimals(self):
        assert CryptoAmount(raw=1, decimals=6) != CryptoAmount(raw=1, decimals=18)


# ---------------------------------------------------------------------------
# TxHash
# ---------------------------------------------------------------------------

VALID_TX_HASH = "0x" + "ab12" * 16

class TestTxHash:
    def test_accepts_valid_hash_lowercase(self):
        tx = TxHash("0x" + "a" * 64)
        assert tx.value == "0x" + "a" * 64

    def test_accepts_valid_hash_uppercase_and_normalizes(self):
        tx = TxHash("0x" + "A" * 64)
        assert tx.value == "0x" + "a" * 64

    def test_accepts_valid_mixed_case_hash(self):
        mixed = "0x" + VALID_TX_HASH[2:].upper()
        tx = TxHash(mixed)
        assert tx.value == VALID_TX_HASH.lower()

    def test_str_returns_lowercased_hash(self):
        tx = TxHash("0x" + "DEAD" * 16)
        assert str(tx) == "0x" + "dead" * 16

    def test_equality_regardless_of_input_case(self):
        a = TxHash("0x" + "a" * 64)
        b = TxHash("0x" + "A" * 64)
        assert a == b

    def test_frozen_raises_on_mutation(self):
        tx = TxHash("0x" + "a" * 64)
        with pytest.raises(FrozenInstanceError):
            tx.value = "0x" + "b" * 64  # type: ignore[misc]

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError, match="Invalid transaction hash"):
            TxHash("")

    def test_rejects_without_0x_prefix(self):
        with pytest.raises(ValueError, match="Invalid transaction hash"):
            TxHash("a" * 64)

    def test_rejects_too_short(self):
        with pytest.raises(ValueError, match="Invalid transaction hash"):
            TxHash("0x" + "a" * 63)

    def test_rejects_too_long(self):
        with pytest.raises(ValueError, match="Invalid transaction hash"):
            TxHash("0x" + "a" * 65)

    def test_rejects_non_hex_characters(self):
        with pytest.raises(ValueError, match="Invalid transaction hash"):
            TxHash("0x" + "z" * 64)

    def test_rejects_plain_address(self):
        with pytest.raises(ValueError, match="Invalid transaction hash"):
            TxHash(VALID_ADDRESS_CHECKSUM)

    def test_hash_consistent(self):
        a = TxHash("0x" + "a" * 64)
        b = TxHash("0x" + "A" * 64)
        assert hash(a) == hash(b)
