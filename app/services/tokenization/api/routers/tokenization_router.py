from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.services.tokenization.application.template_catalog_service import TemplateCatalogService
from app.services.tokenization.domain.entities.template_status import TemplateStatus
from app.services.tokenization.domain.exceptions import (
    ApprovalRequiredError,
    TemplateAlreadyExistsError,
    TemplateNotArchivableError,
    TemplateNotEditableError,
    TemplateNotFoundError,
    TokenizationError,
)
from app.services.tokenization.api.dependencies import get_template_catalog_service
from app.services.tokenization.api.schemas.template_schemas import (
    ApproveTemplateRequest,
    BumpVersionRequest,
    CreateTemplateRequest,
    TemplateListResponse,
    TemplateResponse,
    TemplateSearchRequest,
    UpdateTemplateRequest,
)


def _template_to_response(template) -> TemplateResponse:
    return TemplateResponse(
        name=template.name,
        description=template.description,
        category=template.category,
        strategy=template.strategy,
        token_standard=template.token_standard,
        status=template.status.value,
        version=template.version.to_string(),
        metadata=template.metadata.model_dump(),
        characteristics=template.characteristics.model_dump(),
        token_model=template.token_model.model_dump(),
        business_rules=[r.model_dump() for r in template.business_rules],
        created_at=template.created_at,
        updated_at=template.updated_at,
        created_by=template.created_by,
        approved_by=template.approved_by,
        approved_at=template.approved_at,
    )


router = APIRouter(prefix="/v1/tokenization", tags=["tokenization"])


@router.post(
    "/templates",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tokenization template",
)
async def create_template(
    email: str = Query(..., description="User email"),
    body: CreateTemplateRequest = Body(...),
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
) -> TemplateResponse:
    try:
        template = await service.create_template(
            email=email,
            name=body.name,
            description=body.description,
            category=body.category,
            strategy=body.strategy,
            token_standard=body.token_standard,
            token_model=body.token_model,
            characteristics=body.characteristics,
            metadata=body.metadata,
            business_rules=body.business_rules,
        )
        return _template_to_response(template)
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except TemplateAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )
    except TokenizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.get(
    "/templates",
    response_model=TemplateListResponse,
    summary="List all templates",
)
async def list_templates(
    email: str = Query(..., description="User email"),
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
) -> TemplateListResponse:
    try:
        templates = await service.list_templates(email)
        return TemplateListResponse(
            items=[_template_to_response(t) for t in templates],
            total=len(templates),
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except TokenizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.get(
    "/templates/{name}",
    response_model=TemplateResponse,
    summary="Get a template by name",
)
async def get_template(
    name: str,
    email: str = Query(..., description="User email"),
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
) -> TemplateResponse:
    try:
        template = await service.get_template(email, name)
        return _template_to_response(template)
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except TokenizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.put(
    "/templates/{name}",
    response_model=TemplateResponse,
    summary="Update an existing template",
)
async def update_template(
    name: str,
    email: str = Query(..., description="User email"),
    body: UpdateTemplateRequest = Body(...),
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
) -> TemplateResponse:
    try:
        template = await service.update_template(
            email=email,
            name=name,
            description=body.description,
            category=body.category,
            strategy=body.strategy,
            token_standard=body.token_standard,
            token_model=body.token_model,
            characteristics=body.characteristics,
            metadata=body.metadata,
            business_rules=body.business_rules,
        )
        return _template_to_response(template)
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except TemplateNotEditableError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except TokenizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.delete(
    "/templates/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive a template",
)
async def archive_template(
    name: str,
    email: str = Query(..., description="User email"),
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
) -> None:
    try:
        await service.archive_template(email, name)
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except TemplateNotArchivableError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except TokenizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.post(
    "/templates/{name}/submit",
    response_model=TemplateResponse,
    summary="Submit template for review",
)
async def submit_for_review(
    name: str,
    email: str = Query(..., description="User email"),
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
) -> TemplateResponse:
    try:
        template = await service.submit_for_review(email, name)
        return _template_to_response(template)
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except TemplateNotEditableError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except TokenizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.post(
    "/templates/{name}/approve",
    response_model=TemplateResponse,
    summary="Approve a template",
)
async def approve_template(
    name: str,
    email: str = Query(..., description="User email"),
    body: ApproveTemplateRequest = Body(...),
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
) -> TemplateResponse:
    try:
        template = await service.approve_template(email, name, body.approved_by)
        return _template_to_response(template)
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except TemplateNotEditableError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except TokenizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.post(
    "/templates/{name}/activate",
    response_model=TemplateResponse,
    summary="Activate an approved template",
)
async def activate_template(
    name: str,
    email: str = Query(..., description="User email"),
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
) -> TemplateResponse:
    try:
        template = await service.activate_template(email, name)
        return _template_to_response(template)
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except ApprovalRequiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except TokenizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.post(
    "/templates/{name}/deprecate",
    response_model=TemplateResponse,
    summary="Deprecate a template",
)
async def deprecate_template(
    name: str,
    email: str = Query(..., description="User email"),
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
) -> TemplateResponse:
    try:
        template = await service.deprecate_template(email, name)
        return _template_to_response(template)
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except TokenizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.post(
    "/templates/{name}/version",
    response_model=TemplateResponse,
    summary="Bump template version",
)
async def bump_version(
    name: str,
    email: str = Query(..., description="User email"),
    body: BumpVersionRequest = Body(...),  # noqa: B008
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
) -> TemplateResponse:
    try:
        template = await service.bump_version(email, name, body.bump_type)
        return _template_to_response(template)
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except TokenizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.post(
    "/templates/search",
    response_model=TemplateListResponse,
    summary="Search and filter templates",
)
async def search_templates(
    email: str = Query(..., description="User email"),
    body: TemplateSearchRequest = Body(...),
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
) -> TemplateListResponse:
    try:
        status_filter = None
        if body.status:
            status_filter = TemplateStatus(body.status)

        templates = await service.search_templates(
            email=email,
            query=body.query,
            category=body.category,
            strategy=body.strategy,
            token_standard=body.token_standard,
            status=status_filter,
            tags=body.tags,
            industry=body.industry,
        )
        return TemplateListResponse(
            items=[_template_to_response(t) for t in templates],
            total=len(templates),
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except TokenizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.get(
    "/templates/category/{category}",
    response_model=TemplateListResponse,
    summary="List templates by category",
)
async def list_by_category(
    category: str,
    email: str = Query(..., description="User email"),
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
) -> TemplateListResponse:
    try:
        templates = await service.list_by_category(email, category)
        return TemplateListResponse(
            items=[_template_to_response(t) for t in templates],
            total=len(templates),
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except TokenizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.get(
    "/templates/strategy/{strategy}",
    response_model=TemplateListResponse,
    summary="List templates by strategy",
)
async def list_by_strategy(
    strategy: str,
    email: str = Query(..., description="User email"),
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
) -> TemplateListResponse:
    try:
        templates = await service.list_by_strategy(email, strategy)
        return TemplateListResponse(
            items=[_template_to_response(t) for t in templates],
            total=len(templates),
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except TokenizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )


@router.get(
    "/catalog/seed",
    summary="Seed the catalog with initial templates",
)
async def seed_catalog(
    email: str = Query(..., description="User email"),
    service: TemplateCatalogService = Depends(get_template_catalog_service),  # noqa: B008
):
    from ...infrastructure.seed_data import seed_catalog

    try:
        seeded = await seed_catalog(email, service)
        return {
            "seeded": len(seeded),
            "templates": [_template_to_response(t) for t in seeded],
        }
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
