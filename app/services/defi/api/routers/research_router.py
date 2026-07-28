import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...application.research_report_service import ResearchReportService
from ...domain.entities.research_report import ResearchReport
from ...domain.exceptions import ResearchReportNotFoundError
from ..dependencies import get_research_report_service
from ..schemas.research import (
    ResearchListResponse,
    ResearchPublishRequest,
    ResearchReportResponse,
    ResearchSearchResponse,
)

router = APIRouter(prefix="/v1/defi/research", tags=["defi/research"])


def _to_response(report: ResearchReport) -> ResearchReportResponse:
    return ResearchReportResponse(
        slug=report.slug,
        title=report.title,
        body_markdown=report.body_markdown,
        summary=report.summary,
        published_at=report.published_at,
        categories=report.categories,
        tags=report.tags,
        version=report.version,
        author_type=report.author_type,
    )


@router.post("", response_model=ResearchReportResponse, status_code=status.HTTP_201_CREATED)
async def publish_report(
    body: ResearchPublishRequest,
    service: ResearchReportService = Depends(get_research_report_service),
) -> ResearchReportResponse:
    report = await service.publish(body.model_dump())
    return _to_response(report)


@router.get("", response_model=ResearchListResponse)
async def list_reports(
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    service: ResearchReportService = Depends(get_research_report_service),
) -> ResearchListResponse:
    if category:
        items = await service.list_by_category(category)
    elif tag:
        items = await service.list_by_tag(tag)
    else:
        items = await service.search("")
    return ResearchListResponse(items=[_to_response(r) for r in items], total=len(items))


@router.get("/search", response_model=ResearchSearchResponse)
async def search_reports(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    service: ResearchReportService = Depends(get_research_report_service),
) -> ResearchSearchResponse:
    items = await service.search(q, limit=limit)
    return ResearchSearchResponse(items=[_to_response(r) for r in items], total=len(items))


@router.get("/{slug}", response_model=ResearchReportResponse)
async def get_report(
    slug: str,
    service: ResearchReportService = Depends(get_research_report_service),
) -> ResearchReportResponse:
    try:
        report = await service.get_by_slug(slug)
    except ResearchReportNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return _to_response(report)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    slug: str,
    service: ResearchReportService = Depends(get_research_report_service),
) -> None:
    await service.delete_by_slug(slug)
