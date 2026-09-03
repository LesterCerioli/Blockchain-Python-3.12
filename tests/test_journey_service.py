import pytest
from app.services.tokenization.application.diagnosis_service import DiagnosisService
from app.services.tokenization.application.journey_service import JourneyService
from app.services.tokenization.application.recommendation_service import (
    RecommendationService,
)
from app.services.tokenization.domain.entities.business_objective import BusinessObjective
from app.services.tokenization.domain.entities.journey_enums import ObjectiveCategory
from app.services.tokenization.infrastructure.repositories.in_memory_template_repository import (
    InMemoryTemplateRepository,
)


class TestJourneyService:
    def setup_method(self):
        self.repo = InMemoryTemplateRepository()
        self.diagnosis_service = DiagnosisService()
        self.recommendation_service = RecommendationService(self.repo)
        self.journey_service = JourneyService(
            self.diagnosis_service, self.recommendation_service,
        )

    @pytest.mark.asyncio
    async def test_start_journey(self):
        objective = BusinessObjective(
            description="We need to improve customer loyalty and reduce churn.",
            industry="retail",
        )
        diagnosis, strategies = await self.journey_service.start_journey(objective)
        assert diagnosis.primary_category == ObjectiveCategory.CUSTOMER_LOYALTY
        assert len(strategies) > 0
        assert strategies[0].strategy_code == "loyalty-tokenization"

    @pytest.mark.asyncio
    async def test_select_strategy(self):
        objective = BusinessObjective(
            description="We need to improve customer loyalty and reduce churn.",
            industry="retail",
        )
        diagnosis = self.diagnosis_service.diagnose(objective)
        templates, strategy = await self.journey_service.select_strategy(
            objective, diagnosis, "loyalty-tokenization",
        )
        assert strategy is not None
        assert strategy.strategy_code == "loyalty-tokenization"
        assert len(templates) > 0

    @pytest.mark.asyncio
    async def test_select_strategy_not_found(self):
        objective = BusinessObjective(
            description="We need to improve customer loyalty and reduce churn.",
            industry="retail",
        )
        diagnosis = self.diagnosis_service.diagnose(objective)
        templates, strategy = await self.journey_service.select_strategy(
            objective, diagnosis, "nonexistent-strategy",
        )
        assert strategy is None
        assert templates == []

    @pytest.mark.asyncio
    async def test_select_template(self):
        objective = BusinessObjective(
            description="We need to improve customer loyalty and reduce churn.",
            industry="retail",
        )
        diagnosis = self.diagnosis_service.diagnose(objective)
        strategies = await self.recommendation_service.recommend_strategies(
            objective, diagnosis,
        )
        templates = await self.recommendation_service.recommend_templates(
            objective, diagnosis, strategies[0],
        )
        plan = await self.journey_service.select_template(
            objective, diagnosis, strategies[0], templates[0].template_id,
        )
        assert plan.plan_id is not None
        assert plan.selected_strategy == strategies[0].strategy_name
        assert plan.selected_template_name == templates[0].template_name

    @pytest.mark.asyncio
    async def test_select_template_not_found(self):
        objective = BusinessObjective(
            description="We need to improve customer loyalty and reduce churn.",
            industry="retail",
        )
        diagnosis = self.diagnosis_service.diagnose(objective)
        strategies = await self.recommendation_service.recommend_strategies(
            objective, diagnosis,
        )
        with pytest.raises(ValueError, match="not found"):
            await self.journey_service.select_template(
                objective, diagnosis, strategies[0], "nonexistent-template",
            )

    @pytest.mark.asyncio
    async def test_get_fallback_options(self):
        options = await self.journey_service.get_fallback_options()
        assert "message" in options
        assert "options" in options
        assert len(options["options"]) > 0
        assert "diagnosis_hint" in options

    @pytest.mark.asyncio
    async def test_full_journey_flow(self):
        objective = BusinessObjective(
            description="We need to improve customer loyalty and reduce churn.",
            industry="retail",
        )
        diagnosis, strategies = await self.journey_service.start_journey(objective)
        assert len(strategies) > 0

        templates, strategy = await self.journey_service.select_strategy(
            objective, diagnosis, strategies[0].strategy_code,
        )
        assert len(templates) > 0

        plan = await self.journey_service.select_template(
            objective, diagnosis, strategy, templates[0].template_id,
        )
        assert plan.plan_id is not None
        assert len(plan.steps) > 0
        assert plan.requires_authorization is True

    @pytest.mark.asyncio
    async def test_journey_with_different_objectives(self):
        objectives = [
            BusinessObjective(
                description="We want to tokenize our real estate portfolio.",
                industry="finance",
            ),
            BusinessObjective(
                description="We need to implement decentralized governance.",
                industry="dao",
            ),
            BusinessObjective(
                description="We want to create a DeFi lending protocol.",
                industry="defi",
            ),
        ]

        for objective in objectives:
            diagnosis, strategies = await self.journey_service.start_journey(objective)
            assert len(strategies) > 0
            templates, strategy = await self.journey_service.select_strategy(
                objective, diagnosis, strategies[0].strategy_code,
            )
            assert len(templates) > 0
