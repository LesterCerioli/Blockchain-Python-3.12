from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.auth.api.dependencies import get_current_token
from app.services.tokenization.api.schemas.journey_schemas import (
    FallbackResponse,
    ObjectiveInputRequest,
    SelectStrategyRequest,
    SelectStrategyResponse,
    SelectTemplateRequest,
    SelectTemplateResponse,
    StartJourneyResponse,
    StrategyRecommendationResponse,
    TemplateRecommendationResponse,
    TokenizationPlanResponse,
)
from app.services.tokenization.application.diagnosis_service import DiagnosisService
from app.services.tokenization.application.journey_service import JourneyService
from app.services.tokenization.application.recommendation_service import (
    RecommendationService,
)
from app.services.tokenization.domain.entities.business_objective import BusinessObjective
from app.services.tokenization.infrastructure.repositories.in_memory_template_repository import (
    InMemoryTemplateRepository,
)

router = APIRouter(
    prefix="/tokenization/journey",
    tags=["Tokenization Journey"],
)

_in_memory_repo = InMemoryTemplateRepository()
_diagnosis_service = DiagnosisService()
_recommendation_service = RecommendationService(_in_memory_repo)
_journey_service = JourneyService(_diagnosis_service, _recommendation_service)


@router.post(
    "/start",
    response_model=StartJourneyResponse,
    summary="Start the tokenization journey",
    description=(
        "Analyze a natural-language business objective and return a diagnosis "
        "with recommended tokenization strategies."
    ),
)
async def start_journey(
    request: ObjectiveInputRequest,
    _token: dict = Depends(get_current_token),
) -> StartJourneyResponse:
    objective = BusinessObjective(
        description=request.description,
        industry=request.industry,
        company_size=request.company_size,
        budget_range=request.budget_range,
        timeline_months=request.timeline_months,
        existing_token=request.existing_token,
        target_audience=request.target_audience,
    )

    diagnosis, strategies = await _journey_service.start_journey(objective)

    if not strategies:
        fallback = await _journey_service.get_fallback_options()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=fallback,
        )

    return StartJourneyResponse(
        diagnosis=_diagnosis_to_response(diagnosis),
        strategies=[_strategy_to_response(s) for s in strategies],
        message=(
            f"We identified your objective as '{diagnosis.primary_category.value}' "
            f"with {diagnosis.confidence.value} confidence. "
            f"Here are {len(strategies)} recommended strategies."
        ),
    )


@router.post(
    "/select-strategy",
    response_model=SelectStrategyResponse,
    summary="Select a strategy and see template matches",
    description=(
        "After reviewing strategies, select one to see matching templates."
    ),
)
async def select_strategy(
    request: SelectStrategyRequest,
    objective: ObjectiveInputRequest = Depends(),
    _token: dict = Depends(get_current_token),
) -> SelectStrategyResponse:
    obj = BusinessObjective(
        description=objective.description,
        industry=objective.industry,
        company_size=objective.company_size,
        budget_range=objective.budget_range,
        timeline_months=objective.timeline_months,
        existing_token=objective.existing_token,
        target_audience=objective.target_audience,
    )

    diagnosis = _diagnosis_service.diagnose(obj)
    templates, strategy = await _journey_service.select_strategy(
        obj, diagnosis, request.strategy_code,
    )

    if strategy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{request.strategy_code}' not found",
        )

    if not templates:
        fallback = await _journey_service.get_fallback_options()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=fallback,
        )

    return SelectStrategyResponse(
        strategy=_strategy_to_response(strategy),
        templates=[_template_to_response(t) for t in templates],
        message=(
            f"Selected '{strategy.strategy_name}'. "
            f"Here are {len(templates)} matching templates."
        ),
    )


@router.post(
    "/select-template",
    response_model=SelectTemplateResponse,
    summary="Select a template and generate a plan",
    description=(
        "After reviewing templates, select one to generate a tokenization plan."
    ),
)
async def select_template(
    request: SelectTemplateRequest,
    objective: ObjectiveInputRequest = Depends(),
    strategy_code: str = "",
    _token: dict = Depends(get_current_token),
) -> SelectTemplateResponse:
    obj = BusinessObjective(
        description=objective.description,
        industry=objective.industry,
        company_size=objective.company_size,
        budget_range=objective.budget_range,
        timeline_months=objective.timeline_months,
        existing_token=objective.existing_token,
        target_audience=objective.target_audience,
    )

    diagnosis = _diagnosis_service.diagnose(obj)
    strategies = await _recommendation_service.recommend_strategies(obj, diagnosis)

    selected_strategy = None
    if strategy_code:
        selected_strategy = next(
            (s for s in strategies if s.strategy_code == strategy_code), None,
        )
    if selected_strategy is None and strategies:
        selected_strategy = strategies[0]

    if selected_strategy is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No strategy selected. Provide a strategy_code.",
        )

    plan = await _journey_service.select_template(
        obj, diagnosis, selected_strategy, request.template_id, request.customization,
    )

    return SelectTemplateResponse(
        plan=_plan_to_response(plan),
        message=(
            f"Plan generated for '{plan.selected_template_name}'. "
            f"Review the plan and authorize to proceed."
        ),
        authorization_required=plan.requires_authorization,
    )


@router.get(
    "/fallback",
    response_model=FallbackResponse,
    summary="Get fallback options",
    description="Returns alternative options when no suitable template is found.",
)
async def get_fallback_options(
    _token: dict = Depends(get_current_token),
) -> FallbackResponse:
    options = await _journey_service.get_fallback_options()
    return FallbackResponse(**options)


@router.get(
    "/objectives",
    summary="List available objective categories",
    description="Returns all supported business objective categories.",
)
async def list_objective_categories(
    _token: dict = Depends(get_current_token),
) -> list[dict]:
    from app.services.tokenization.domain.entities.journey_enums import ObjectiveCategory
    return [
        {"code": cat.value, "name": cat.value.replace("_", " ").title()}
        for cat in ObjectiveCategory
    ]


def _diagnosis_to_response(diagnosis) -> dict:
    return {
        "primary_category": diagnosis.primary_category.value,
        "secondary_categories": [c.value for c in diagnosis.secondary_categories],
        "confidence": diagnosis.confidence.value,
        "confidence_score": diagnosis.confidence_score,
        "keywords_found": [
            {"keyword": kw.keyword, "weight": kw.weight, "context": kw.context}
            for kw in diagnosis.keywords_found
        ],
        "pain_points": diagnosis.pain_points,
        "goals": diagnosis.goals,
        "reasoning": diagnosis.reasoning,
    }


def _strategy_to_response(strategy) -> dict:
    return {
        "strategy_code": strategy.strategy_code,
        "strategy_name": strategy.strategy_name,
        "description": strategy.description,
        "fit": strategy.fit.value,
        "fit_score": strategy.fit_score,
        "why_recommended": strategy.why_recommended,
        "expected_outcomes": strategy.expected_outcomes,
        "considerations": strategy.considerations,
        "prerequisites": strategy.prerequisites,
        "estimated_complexity": strategy.estimated_complexity,
        "estimated_timeline_months": strategy.estimated_timeline_months,
    }


def _template_to_response(template) -> dict:
    return {
        "template_id": template.template_id,
        "template_name": template.template_name,
        "description": template.description,
        "token_standard": template.token_standard,
        "category": template.category,
        "strategy": template.strategy,
        "fit": template.fit.value,
        "fit_score": template.fit_score,
        "why_recommended": template.why_recommended,
        "key_features": template.key_features,
        "customization_options": template.customization_options,
        "limitations": template.limitations,
        "is_derived": template.is_derived,
        "parent_template_id": template.parent_template_id,
    }


def _plan_to_response(plan) -> dict:
    return {
        "plan_id": plan.plan_id,
        "journey_status": plan.journey_status,
        "objective_description": plan.objective_description,
        "diagnosis_summary": plan.diagnosis_summary,
        "selected_strategy": plan.selected_strategy,
        "selected_template_name": plan.selected_template_name,
        "customization_summary": plan.customization_summary,
        "steps": [
            {
                "step_number": step.step_number,
                "title": step.title,
                "description": step.description,
                "estimated_duration": step.estimated_duration,
                "dependencies": step.dependencies,
                "requires_approval": step.requires_approval,
            }
            for step in plan.steps
        ],
        "estimated_total_timeline": plan.estimated_total_timeline,
        "estimated_cost_range": plan.estimated_cost_range,
        "risks": plan.risks,
        "next_actions": plan.next_actions,
        "requires_authorization": plan.requires_authorization,
    }
