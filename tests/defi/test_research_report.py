import sys
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.defi.domain.entities.research_report import ResearchReport
from app.services.defi.application.research_report_service import ResearchReportService
from app.services.defi.domain.exceptions import ResearchReportNotFoundError
from app.services.defi.infrastructure.persistence.in_memory_research_report_repository import (
    InMemoryResearchReportRepository,
)


def _valid_payload(**overrides) -> dict:
    base = {
        "report_id": str(uuid4()),
        "title": "Q3 2024 DeFi Market Overview",
        "body_markdown": "# Market Report\n\nThe DeFi market has shown resilience...",
        "summary": "Q3 2024 saw a 12% increase in TVL across major protocols.",
        "published_at": datetime.now(tz=timezone.utc).isoformat(),
        "categories": ["market-analysis", "tvl"],
        "tags": ["defi", "ethereum", "tvl"],
        "version": 1,
        "author_type": "editorial",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Entity: field validation
# ---------------------------------------------------------------------------

def test_entity_accepts_valid_payload():
    report = ResearchReport.model_validate(_valid_payload())
    assert report.title == "Q3 2024 DeFi Market Overview"
    assert report.author_type == "editorial"
    assert report.version == 1


def test_entity_rejects_user_id_in_payload():
    payload = _valid_payload(user_id=str(uuid4()))
    with pytest.raises(ValidationError) as exc_info:
        ResearchReport.model_validate(payload)
    assert "user_id" in str(exc_info.value)


def test_entity_rejects_author_type_user():
    payload = _valid_payload(author_type="user")
    with pytest.raises(ValidationError) as exc_info:
        ResearchReport.model_validate(payload)
    assert "author_type" in str(exc_info.value) or "user" in str(exc_info.value)


def test_entity_accepts_automated_author_type():
    payload = _valid_payload(author_type="automated")
    report = ResearchReport.model_validate(payload)
    assert report.author_type == "automated"


def test_entity_rejects_title_over_200_chars():
    payload = _valid_payload(title="x" * 201)
    with pytest.raises(ValidationError):
        ResearchReport.model_validate(payload)


def test_entity_rejects_summary_over_500_chars():
    payload = _valid_payload(summary="x" * 501)
    with pytest.raises(ValidationError):
        ResearchReport.model_validate(payload)


def test_entity_rejects_blank_title():
    payload = _valid_payload(title="   ")
    with pytest.raises(ValidationError):
        ResearchReport.model_validate(payload)


def test_entity_rejects_empty_categories():
    payload = _valid_payload(categories=[])
    with pytest.raises(ValidationError):
        ResearchReport.model_validate(payload)


def test_entity_rejects_empty_tags():
    payload = _valid_payload(tags=[])
    with pytest.raises(ValidationError):
        ResearchReport.model_validate(payload)


def test_entity_rejects_version_zero():
    payload = _valid_payload(version=0)
    with pytest.raises(ValidationError):
        ResearchReport.model_validate(payload)


def test_entity_is_frozen():
    report = ResearchReport.model_validate(_valid_payload())
    with pytest.raises(Exception):
        report.title = "changed"


def test_entity_auto_generates_slug_from_title():
    report = ResearchReport.model_validate(_valid_payload())
    assert report.slug == "q3-2024-defi-market-overview"


def test_entity_accepts_explicit_slug():
    payload = _valid_payload(slug="my-custom-slug")
    report = ResearchReport.model_validate(payload)
    assert report.slug == "my-custom-slug"


# ---------------------------------------------------------------------------
# Entity: forbidden fields
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("forbidden_field", ["user_id", "wallet_address", "subscriber_id", "personalized_for"])
def test_entity_rejects_all_forbidden_fields(forbidden_field):
    payload = _valid_payload(**{forbidden_field: "forbidden_value"})
    with pytest.raises(ValidationError) as exc_info:
        ResearchReport.model_validate(payload)
    assert forbidden_field in str(exc_info.value)


# ---------------------------------------------------------------------------
# Service: publish guard
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_service_publish_rejects_user_id():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    payload = _valid_payload(user_id=str(uuid4()))
    with pytest.raises((ValueError, ValidationError)) as exc_info:
        await service.publish(payload)
    assert "user_id" in str(exc_info.value)


@pytest.mark.asyncio
async def test_service_publish_rejects_wallet_address():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    payload = _valid_payload(wallet_address="0x1234")
    with pytest.raises((ValueError, ValidationError)):
        await service.publish(payload)


@pytest.mark.asyncio
async def test_service_publish_rejects_subscriber_id():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    payload = _valid_payload(subscriber_id="sub_123")
    with pytest.raises((ValueError, ValidationError)):
        await service.publish(payload)


@pytest.mark.asyncio
async def test_service_publish_rejects_personalized_for():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    payload = _valid_payload(personalized_for="user_abc")
    with pytest.raises((ValueError, ValidationError)):
        await service.publish(payload)


@pytest.mark.asyncio
async def test_service_publish_rejects_author_type_user():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    payload = _valid_payload(author_type="user")
    with pytest.raises((ValueError, ValidationError)):
        await service.publish(payload)


@pytest.mark.asyncio
async def test_service_publish_succeeds_with_valid_payload():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    payload = _valid_payload()
    report = await service.publish(payload)
    assert report.report_id is not None
    stored = await repo.get_by_id(report.report_id)
    assert stored is not None
    assert stored.title == report.title


@pytest.mark.asyncio
async def test_service_publish_does_not_store_user_id():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    payload = _valid_payload(user_id=str(uuid4()))
    try:
        await service.publish(payload)
    except (ValueError, ValidationError):
        pass
    assert len(repo._store) == 0


# ---------------------------------------------------------------------------
# Service: get / list / search / delete
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_service_get_by_id_returns_report():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    report = await service.publish(_valid_payload())
    fetched = await service.get_by_id(report.report_id)
    assert fetched.title == report.title


@pytest.mark.asyncio
async def test_service_get_by_id_raises_not_found():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    with pytest.raises(ResearchReportNotFoundError):
        await service.get_by_id(uuid4())


@pytest.mark.asyncio
async def test_service_list_by_category():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    await service.publish(_valid_payload())
    await service.publish(_valid_payload(
        report_id=str(uuid4()),
        categories=["staking", "yields"],
    ))
    results = await service.list_by_category("staking")
    assert len(results) == 1


@pytest.mark.asyncio
async def test_service_list_by_tag():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    await service.publish(_valid_payload())
    results = await service.list_by_tag("ethereum")
    assert len(results) == 1


@pytest.mark.asyncio
async def test_service_search_fts():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    await service.publish(_valid_payload(
        title="Ethereum Staking Yields Q3",
        body_markdown="Ethereum staking has yielded strong returns...",
        tags=["ethereum", "staking"],
    ))
    await service.publish(_valid_payload(
        report_id=str(uuid4()),
        title="Solana Ecosystem Growth",
        body_markdown="Solana has grown rapidly...",
        tags=["solana", "ecosystem"],
    ))
    results = await service.search("ethereum")
    assert len(results) == 1
    assert "Ethereum" in results[0].title


@pytest.mark.asyncio
async def test_service_search_fts_no_results():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    await service.publish(_valid_payload())
    results = await service.search("nonexistent_term_xyz")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_service_delete_removes_report():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    report = await service.publish(_valid_payload())
    await service.delete(report.report_id)
    fetched = await repo.get_by_id(report.report_id)
    assert fetched is None


# ---------------------------------------------------------------------------
# Service: slug-based operations
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_service_get_by_slug_returns_report():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    report = await service.publish(_valid_payload())
    fetched = await service.get_by_slug(report.slug)
    assert fetched.title == report.title


@pytest.mark.asyncio
async def test_service_get_by_slug_raises_not_found():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    with pytest.raises(ResearchReportNotFoundError):
        await service.get_by_slug("nonexistent-slug")


@pytest.mark.asyncio
async def test_service_delete_by_slug_removes_report():
    repo = InMemoryResearchReportRepository()
    service = ResearchReportService(repository=repo)
    report = await service.publish(_valid_payload())
    await service.delete_by_slug(report.slug)
    fetched = await repo.get_by_slug(report.slug)
    assert fetched is None
