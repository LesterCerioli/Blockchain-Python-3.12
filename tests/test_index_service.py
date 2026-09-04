import asyncio
from decimal import Decimal

from app.services.defi.application.index_service import IndexService
from app.services.defi.domain.exceptions import IndexNotFoundError


def test_list_indices_includes_required() -> None:
    svc = IndexService()
    indices = asyncio.run(svc.list_indices())
    ids = {index.index_id for index in indices}
    assert "defi-tvl-top20" in ids
    assert "top100-market-cap" in ids


def test_get_index_ok_and_missing() -> None:
    svc = IndexService()
    index = asyncio.run(svc.get_index("defi-tvl-top20"))
    assert index.index_id == "defi-tvl-top20"

    raised = False
    try:
        asyncio.run(svc.get_index("does-not-exist"))
    except IndexNotFoundError:
        raised = True
    assert raised, "IndexNotFoundError expected for unknown code"


def test_token_rankings_pagination_and_shape() -> None:
    svc = IndexService()
    page = asyncio.run(svc.get_token_rankings("price", None, 1, 10))
    assert page.page == 1
    assert page.page_size == 10
    assert page.total >= 0
    assert len(page.items) <= 10
    for ranking in page.items:
        assert ranking.rank >= 1
        assert isinstance(ranking.value, Decimal)
        assert ranking.metric == "price"


def test_protocol_rankings_shape() -> None:
    svc = IndexService()
    rankings = asyncio.run(svc.get_protocol_rankings("tvl", None))
    assert isinstance(rankings, list)
    for ranking in rankings:
        assert ranking.rank >= 1
        assert isinstance(ranking.value, Decimal)
        assert ranking.metric == "tvl"
