from fastapi import Request

from ..application.quote_service import QuoteService
from ..application.research_report_service import ResearchReportService


def get_quote_service(request: Request) -> QuoteService:
    return request.app.state.defi_quote_service


def get_research_report_service(request: Request) -> ResearchReportService:
    return request.app.state.defi_research_service
