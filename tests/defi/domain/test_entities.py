from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.services.defi.domain.entities import (
    MarketIndex,
    Quote,
    ResearchReport,
    UnsignedTransaction,
    WalletSession,
)

# ---------------------------------------------------------------------------
# Quote
# ---------------------------------------------------------------------------

def test_quote_valid():
    q = Quote(
        token_in="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        token_out="0xdAC17F958D2ee523a2206206994597C13D831ec7",
        amount_in=Decimal("100.00"),
        amount_out=Decimal("99.95"),
        price_impact_bps=5,
        slippage_bps=50,
        chain_id=1,
    )
    assert q.token_in == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    assert q.token_out == "0xdac17f958d2ee523a2206206994597c13d831ec7"


# ---------------------------------------------------------------------------
# MarketIndex
# ---------------------------------------------------------------------------

def test_market_index_valid():
    idx = MarketIndex(
        symbol="defi100",
        name="DeFi 100 Index",
        value=Decimal("1234.56"),
        timestamp=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    assert idx.symbol == "DEFI100"


def test_market_index_blank_symbol_raises():
    with pytest.raises(ValidationError):
        MarketIndex(
            symbol="   ",
            name="DeFi 100 Index",
            value=Decimal("1234.56"),
            timestamp=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )


# ---------------------------------------------------------------------------
# WalletSession
# ---------------------------------------------------------------------------

def test_wallet_session_valid():
    ws = WalletSession(
        wallet_address="0xAbCd1234567890abcdef1234567890abcdef1234",
        session_id="sess-001",
        chain_id=1,
    )
    assert ws.wallet_address == "0xabcd1234567890abcdef1234567890abcdef1234"


def test_wallet_session_rejects_private_key_format():
    private_key = "a" * 64
    with pytest.raises(ValidationError, match="private key"):
        WalletSession(wallet_address=private_key, session_id="sess-001", chain_id=1)


def test_wallet_session_rejects_private_key_with_0x_prefix():
    private_key = "0x" + "b" * 64
    with pytest.raises(ValidationError, match="private key"):
        WalletSession(wallet_address=private_key, session_id="sess-001", chain_id=1)


# ---------------------------------------------------------------------------
# UnsignedTransaction
# ---------------------------------------------------------------------------

def test_unsigned_transaction_valid():
    tx = UnsignedTransaction(
        to="0xdac17f958d2ee523a2206206994597c13d831ec7",
        from_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        value=Decimal("0"),
        gas=21_000,
        gas_price=Decimal("20000000000"),
        nonce=0,
        chain_id=1,
    )
    assert tx.chain_id == 1


@pytest.mark.parametrize("signing_field", ["v", "r", "s"])
def test_unsigned_transaction_rejects_signing_fields(signing_field: str):
    with pytest.raises(ValidationError, match="Signing fields"):
        UnsignedTransaction(
            **{
                "to": "0xdac17f958d2ee523a2206206994597c13d831ec7",
                "from_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                "value": Decimal("0"),
                "gas": 21_000,
                "gas_price": Decimal("20000000000"),
                "nonce": 0,
                "chain_id": 1,
                signing_field: "0xdeadbeef",
            }
        )


# ---------------------------------------------------------------------------
# ResearchReport
# ---------------------------------------------------------------------------

def test_research_report_valid():
    report = ResearchReport(
        title="ETH Q3 2026 Outlook",
        summary="Bullish on layer-2 adoption.",
        target_token="eth",
        price_target=Decimal("4500.00"),
        published_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    assert report.target_token == "ETH"


def test_research_report_blank_title_raises():
    with pytest.raises(ValidationError):
        ResearchReport(
            title="   ",
            summary="Some summary.",
            target_token="ETH",
            price_target=Decimal("4500.00"),
            published_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
