from __future__ import annotations

from pydantic import BaseModel, Field

from app.services.tokenization.application.diagnosis_service import DiagnosisService
from app.services.tokenization.application.recommendation_service import (
    RecommendationService,
)
from app.services.tokenization.domain.entities.business_objective import BusinessObjective
from app.services.tokenization.domain.entities.diagnosis import Diagnosis
from app.services.tokenization.domain.entities.journey_enums import JourneyStatus
from app.services.tokenization.domain.entities.strategy_recommendation import (
    StrategyRecommendation,
)
from app.services.tokenization.domain.entities.template_recommendation import (
    TemplateRecommendation,
)
from app.services.tokenization.domain.entities.tokenization_plan import TokenizationPlan


class JourneyState(BaseModel):
    status: JourneyStatus
    objective: BusinessObjective | None = None
    diagnosis: Diagnosis | None = None
    strategies: list[StrategyRecommendation] = Field(default_factory=list)
    selected_strategy_code: str | None = None
    templates: list[TemplateRecommendation] = Field(default_factory=list)
    selected_template_id: str | None = None
    customization: dict = Field(default_factory=dict)
    plan: TokenizationPlan | None = None


class JourneyService:
    """Orchestrates the full tokenization journey from objective to plan."""

    def __init__(
        self,
        diagnosis_service: DiagnosisService,
        recommendation_service: RecommendationService,
    ) -> None:
        self._diagnosis = diagnosis_service
        self._recommendation = recommendation_service

    async def start_journey(
        self,
        objective: BusinessObjective,
    ) -> tuple[Diagnosis, list[StrategyRecommendation]]:
        diagnosis = self._diagnosis.diagnose(objective)
        strategies = await self._recommendation.recommend_strategies(objective, diagnosis)
        return diagnosis, strategies

    async def select_strategy(
        self,
        objective: BusinessObjective,
        diagnosis: Diagnosis,
        strategy_code: str,
    ) -> tuple[list[TemplateRecommendation], StrategyRecommendation | None]:
        strategies = await self._recommendation.recommend_strategies(objective, diagnosis)
        selected = next((s for s in strategies if s.strategy_code == strategy_code), None)
        if selected is None:
            return [], None

        templates = await self._recommendation.recommend_templates(
            objective, diagnosis, selected,
        )
        return templates, selected

    async def select_template(
        self,
        objective: BusinessObjective,
        diagnosis: Diagnosis,
        strategy: StrategyRecommendation,
        template_id: str,
        customization: dict | None = None,
    ) -> TokenizationPlan:
        templates = await self._recommendation.recommend_templates(
            objective, diagnosis, strategy,
        )
        selected = next((t for t in templates if t.template_id == template_id), None)
        if selected is None:
            raise ValueError(f"Template {template_id} not found in recommendations")

        plan = await self._recommendation.create_plan(
            objective, diagnosis, strategy, selected, customization,
        )
        return plan

    async def get_fallback_options(self) -> dict:
        return {
            "message": "No suitable template found for your objective.",
            "options": [
                {
                    "action": "create_custom_template",
                    "description": "Create a new template from scratch based on your specific requirements",
                    "endpoint": "POST /tokenization/templates",
                },
                {
                    "action": "modify_existing_template",
                    "description": "Clone an existing template and customize it for your needs",
                    "endpoint": "POST /tokenization/templates/clone",
                },
                {
                    "action": "consult_expert",
                    "description": "Schedule a consultation with our tokenization experts",
                    "endpoint": "POST /tokenization/consultation",
                },
            ],
            "diagnosis_hint": "Your objective may require a custom solution. "
                              "Provide more details about your specific use case "
                              "for a more accurate recommendation.",
        }
