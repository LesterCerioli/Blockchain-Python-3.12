from fastapi import Request

from app.services.tokenization.application.template_catalog_service import TemplateCatalogService


def get_template_catalog_service(request: Request) -> TemplateCatalogService:
    return request.app.state.tokenization_catalog_service
