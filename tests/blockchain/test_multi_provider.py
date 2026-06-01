import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.blockchain.ethereum.infrastructure.providers.multi_provider import MultiProvider


def _make_provider(name: str, priority: int, block_number: int | None):
    p = MagicMock()
    p.name = name
    p.priority = priority
    p.is_available = True
    if block_number is not None:
        p.get_block_number = AsyncMock(return_value=block_number)
        p.get_chain_id = AsyncMock(return_value=1)
        p.is_syncing = AsyncMock(return_value=False)
    else:
        p.get_block_number = AsyncMock(side_effect=ConnectionError("provider down"))
        p.get_chain_id = AsyncMock(side_effect=ConnectionError("provider down"))
        p.is_syncing = AsyncMock(side_effect=ConnectionError("provider down"))
    return p


@pytest.mark.asyncio
async def test_uses_highest_priority_provider():
    primary = _make_provider("primary", priority=1, block_number=20_000_000)
    secondary = _make_provider("secondary", priority=2, block_number=19_999_000)

    mp = MultiProvider([secondary, primary])  # intentionally reversed order

    block = await mp.get_block_number()
    assert block == 20_000_000
    primary.get_block_number.assert_awaited_once()
    secondary.get_block_number.assert_not_awaited()


@pytest.mark.asyncio
async def test_failover_to_secondary_when_primary_fails():
    primary = _make_provider("primary", priority=1, block_number=None)
    secondary = _make_provider("secondary", priority=2, block_number=19_999_000)

    mp = MultiProvider([primary, secondary])

    block = await mp.get_block_number()
    assert block == 19_999_000


@pytest.mark.asyncio
async def test_raises_when_all_providers_fail():
    p1 = _make_provider("p1", priority=1, block_number=None)
    p2 = _make_provider("p2", priority=2, block_number=None)

    mp = MultiProvider([p1, p2])

    with pytest.raises(RuntimeError, match="All.*provider"):
        await mp.get_block_number()


@pytest.mark.asyncio
async def test_skips_unavailable_providers():
    primary = _make_provider("primary", priority=1, block_number=20_000_000)
    primary.is_available = False
    secondary = _make_provider("secondary", priority=2, block_number=19_999_000)

    mp = MultiProvider([primary, secondary])

    block = await mp.get_block_number()
    assert block == 19_999_000
    primary.get_block_number.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_when_no_providers_available():
    p = _make_provider("p1", priority=1, block_number=20_000_000)
    p.is_available = False

    mp = MultiProvider([p])

    with pytest.raises(RuntimeError, match="No Ethereum providers"):
        await mp.get_block_number()
