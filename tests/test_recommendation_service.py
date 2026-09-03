import pytest
from app.services.tokenization.application.diagnosis_service import DiagnosisService
from app.services.tokenization.application.recommendation_service import (
    RecommendationService,
)
from app.services.tokenization.domain.entities.business_objective import BusinessObjective
from app.services.tokenization.domain.entities.journey_enums import (
    ObjectiveCategory,
    StrategyFit,
)
from app.services.tokenization.infrastructure.repositories.in_memory_template_repository import (
    InMemoryTemplateRepository,
)


class TestRecommendationService:
    def setup_method(self):
        self.repo = InMemoryTemplateRepository()
        self.recommendation_service = RecommendationService(self.repo)
        self.diagnosis_service = DiagnosisService()

    @pytest.mark.asyncio
    async def test_recommend_strategies_for_loyalty(self):
        objective = BusinessObjective(
            description="We need to improve customer loyalty and reduce churn.",
            industry="retail",
        )
        diagnosis = self.diagnosis_service.diagnose(objective)
        strategies = await self.recommendation_service.recommend_strategies(
            objective, diagnosis,
        )
        assert len(strategies) > 0
        assert strategies[0].strategy_code == "loyalty-tokenization"
        assert strategies[0].fit in (StrategyFit.EXCELLENT, StrategyFit.GOOD)
        assert len(strategies[0].why_recommended) > 0
        assert len(strategies[0].expected_outcomes) > 0

    @pytest.mark.asyncio
    async def test_recommend_strategies_for_engagement(self):
        objective = BusinessObjective(
            description="We want to increase user engagement through gamification.",
            industry="gaming",
        )
        diagnosis = self.diagnosis_service.diagnose(objective)
        strategies = await self.recommendation_service.recommend_strategies(
            objective, diagnosis,
        )
        assert len(strategies) > 0
        strategy_codes = [s.strategy_code for s in strategies]
        assert "gamified-rewards" in strategy_codes or "social-token" in strategy_codes

    @pytest.mark.asyncio
    async def test_recommend_strategies_for_asset_tokenization(self):
        objective = BusinessObjective(
            description="We want to tokenize our real estate portfolio.",
            industry="finance",
        )
        diagnosis = self.diagnosis_service.diagnose(objective)
        strategies = await self.recommendation_service.recommend_strategies(
            objective, diagnosis,
        )
        assert len(strategies) > 0
        assert strategies[0].strategy_code == "asset-tokenization"

    @pytest.mark.asyncio
    async def test_recommend_strategies_multiple_objectives(self):
        objectives = [
            ("We need to improve customer engagement and increase daily active users.",
             "retail"),
            ("We want to tokenize our real estate portfolio and enable fractional ownership.",
             "finance"),
            ("We need to acquire new customers through referral programs.",
             "saas"),
        ]
        for desc, industry in objectives:
            objective = BusinessObjective(description=desc, industry=industry)
            diagnosis = self.diagnosis_service.diagnose(objective)
            strategies = await self.recommendation_service.recommend_strategies(
                objective, diagnosis,
            )
            assert len(strategies) >= 1
            for i in range(len(strategies) - 1):
                assert strategies[i].fit_score >= strategies[i + 1].fit_score

    @pytest.mark.asyncio
    async def test_recommend_templates_for_loyalty(self):
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
        assert len(templates) > 0
        assert templates[0].fit_score > 0
        assert len(templates[0].why_recommended) > 0
        assert len(templates[0].key_features) > 0

    @pytest.mark.asyncio
    async def test_recommend_templates_sorted_by_fit(self):
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
        for i in range(len(templates) - 1):
            assert templates[i].fit_score >= templates[i + 1].fit_score

    @pytest.mark.asyncio
    async def test_create_plan(self):
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
        plan = await self.recommendation_service.create_plan(
            objective, diagnosis, strategies[0], templates[0],
        )
        assert plan.plan_id is not None
        assert plan.selected_strategy == strategies[0].strategy_name
        assert plan.selected_template_name == templates[0].template_name
        assert len(plan.steps) > 0
        assert plan.requires_authorization is True
        assert plan.estimated_total_timeline is not None
        assert plan.estimated_cost_range is not None
        assert len(plan.risks) > 0
        assert len(plan.next_actions) > 0

    @pytest.mark.asyncio
    async def test_create_plan_with_customization(self):
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
        customization = {
            "token_name": "My Loyalty Token",
            "token_symbol": "MLT",
            "max_supply": 1000000,
        }
        plan = await self.recommendation_service.create_plan(
            objective, diagnosis, strategies[0], templates[0], customization,
        )
        assert plan.customization_summary == customization

    @pytest.mark.asyncio
    async def test_strategy_fit_values(self):
        objective = BusinessObjective(
            description="We need to improve customer loyalty and reduce churn.",
            industry="retail",
        )
        diagnosis = self.diagnosis_service.diagnose(objective)
        strategies = await self.recommendation_service.recommend_strategies(
            objective, diagnosis,
        )
        for strategy in strategies:
            assert strategy.fit in (
                StrategyFit.EXCELLENT,
                StrategyFit.GOOD,
                StrategyFit.FAIR,
                StrategyFit.POOR,
            )
            assert 0 <= strategy.fit_score <= 1

    @pytest.mark.asyncio
    async def test_template_has_features_and_limitations(self):
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
        for template in templates:
            assert len(template.key_features) > 0
            assert len(template.customization_options) > 0
            assert isinstance(template.limitations, list)
