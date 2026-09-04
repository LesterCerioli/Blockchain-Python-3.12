from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.services.auth.api.dependencies import get_current_token
from ...application.recommendation_choice_service import RecommendationChoiceService
from ...domain.entities.business_type import BusinessType
from ..schemas.choice_schemas import (
    BusinessTypesResponse,
    ChoiceCreateRequest,
    ChoiceListResponse,
    ChoiceResponse,
    ReorderRequest,
    ReorderResponse,
    TemplatesByBusinessTypeResponse,
)

router = APIRouter(prefix="/tokenization", tags=["tokenization-choices"])

CREATE_ZERO_OPTION = "Nenhuma destas — Criar do Zero"


async def get_choice_service(request: Request) -> RecommendationChoiceService:
    return request.app.state.choice_service


@router.get(
    "/business-types",
    response_model=BusinessTypesResponse,
    summary="Lista setores disponíveis (Passo 1)",
)
async def list_business_types(
    _token: dict = Depends(get_current_token),
) -> BusinessTypesResponse:
    types = [
        {"value": bt.value, "label": bt.value.replace("_", " ").title()}
        for bt in BusinessType
    ]
    return BusinessTypesResponse(business_types=types)


@router.get(
    "/templates/by-business-type",
    response_model=TemplatesByBusinessTypeResponse,
    summary="Busca templates por business_type (async, não bloqueia)",
)
async def get_templates_by_business_type(
    business_type: BusinessType = Query(...),
    user_id: str = Query(..., min_length=1),
    _token: dict = Depends(get_current_token),
    svc: RecommendationChoiceService = Depends(get_choice_service),
) -> TemplatesByBusinessTypeResponse:
    templates = await svc.get_templates_by_business_type(user_id, business_type)
    return TemplatesByBusinessTypeResponse(
        business_type=business_type.value,
        templates=templates,
        count=len(templates),
    )


@router.post(
    "/recommendation/order",
    response_model=ReorderResponse,
    summary="Passo 3: Consulta Groq para reordenar (só reordena, não inventa)",
)
async def reorder_templates(
    body: ReorderRequest,
    _token: dict = Depends(get_current_token),
    svc: RecommendationChoiceService = Depends(get_choice_service),
) -> ReorderResponse:
    candidates = await svc.get_templates_by_business_type(body.user_id, body.business_type)
    ordered = await svc.reorder_with_groq(body.business_type, body.description, candidates)
    final = ordered + [CREATE_ZERO_OPTION]
    return ReorderResponse(
        business_type=body.business_type.value,
        description=body.description,
        ordered_templates=ordered,
        final_options=final,
    )


@router.post(
    "/choices",
    response_model=ChoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Passo 5: Persiste escolha final em tokenization_templates (DynamoDB + Postgres)",
)
async def create_choice(
    body: ChoiceCreateRequest,
    _token: dict = Depends(get_current_token),
    svc: RecommendationChoiceService = Depends(get_choice_service),
) -> ChoiceResponse:
    try:
        choice = await svc.persist_choice(
            user_id=body.user_id,
            business_type=body.business_type,
            description_tokenization=body.description_tokenization,
            tokenization_template=body.tokenization_template,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return ChoiceResponse(
        id=choice.id,
        user_id=choice.user_id,
        business_type=choice.business_type.value,
        description_tokenization=choice.description_tokenization,
        tokenization_template=choice.tokenization_template,
        chosen_at=choice.chosen_at,
    )


@router.get(
    "/choices",
    response_model=ChoiceListResponse,
    summary="Lista escolhas por user_id (isolamento obrigatório)",
)
async def list_choices(
    user_id: str = Query(..., min_length=1),
    _token: dict = Depends(get_current_token),
    svc: RecommendationChoiceService = Depends(get_choice_service),
) -> ChoiceListResponse:
    items = await svc.get_user_choices(user_id)
    return ChoiceListResponse(
        items=[
            ChoiceResponse(
                id=c.id,
                user_id=c.user_id,
                business_type=c.business_type.value,
                description_tokenization=c.description_tokenization,
                tokenization_template=c.tokenization_template,
                chosen_at=c.chosen_at,
            )
            for c in items
        ],
        total=len(items),
    )
