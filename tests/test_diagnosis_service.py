import pytest
from app.services.tokenization.application.diagnosis_service import DiagnosisService
from app.services.tokenization.domain.entities.business_objective import BusinessObjective
from app.services.tokenization.domain.entities.journey_enums import (
    DiagnosisConfidence,
    ObjectiveCategory,
)


class TestDiagnosisService:
    def setup_method(self):
        self.service = DiagnosisService()

    def test_diagnose_loyalty_objective(self):
        objective = BusinessObjective(
            description="We need to improve customer loyalty and reduce churn. "
                        "Our repeat purchase rate has dropped significantly.",
            industry="retail",
        )
        result = self.service.diagnose(objective)
        assert result.primary_category == ObjectiveCategory.CUSTOMER_LOYALTY
        assert result.confidence in (DiagnosisConfidence.HIGH, DiagnosisConfidence.MEDIUM)
        assert len(result.keywords_found) > 0
        assert len(result.reasoning) > 0

    def test_diagnose_revenue_growth(self):
        objective = BusinessObjective(
            description="We want to increase revenue and monetize our platform "
                        "through subscription tiers and premium features.",
            industry="fintech",
        )
        result = self.service.diagnose(objective)
        assert result.primary_category == ObjectiveCategory.REVENUE_GROWTH
        assert result.confidence_score > 0.3

    def test_diagnose_asset_tokenization(self):
        objective = BusinessObjective(
            description="We want to tokenize our real estate portfolio and enable "
                        "fractional ownership for investors.",
            industry="finance",
        )
        result = self.service.diagnose(objective)
        assert result.primary_category == ObjectiveCategory.ASSET_TOKENIZATION
        assert "tokenize" in [kw.keyword for kw in result.keywords_found]

    def test_diagnose_customer_acquisition(self):
        objective = BusinessObjective(
            description="We need to acquire new customers through referral programs "
                        "and viral growth mechanics.",
            industry="saas",
        )
        result = self.service.diagnose(objective)
        assert result.primary_category == ObjectiveCategory.CUSTOMER_ACQUISITION
        assert "referral" in [kw.keyword for kw in result.keywords_found]

    def test_diagnose_engagement(self):
        objective = BusinessObjective(
            description="We want to increase user engagement and daily active users "
                        "through gamification and reward mechanics.",
            industry="gaming",
        )
        result = self.service.diagnose(objective)
        assert result.primary_category == ObjectiveCategory.CUSTOMER_ENGAGEMENT
        assert any("gamification" in kw.keyword for kw in result.keywords_found)

    def test_diagnose_incentive_model(self):
        objective = BusinessObjective(
            description="We need to create an incentive program that rewards specific "
                        "user behaviors and drives target actions.",
            industry="fintech",
        )
        result = self.service.diagnose(objective)
        assert result.primary_category == ObjectiveCategory.INCENTIVE_MODEL

    def test_diagnose_community_building(self):
        objective = BusinessObjective(
            description="We want to build a strong community and create social tokens "
                        "for our creator economy platform.",
            industry="social",
        )
        result = self.service.diagnose(objective)
        assert result.primary_category == ObjectiveCategory.COMMUNITY_BUILDING

    def test_diagnose_governance(self):
        objective = BusinessObjective(
            description="We need to implement decentralized governance and voting "
                        "for our DAO organization.",
            industry="dao",
        )
        result = self.service.diagnose(objective)
        assert result.primary_category == ObjectiveCategory.GOVERNANCE

    def test_diagnose_financing(self):
        objective = BusinessObjective(
            description="We want to create a DeFi lending protocol with yield-bearing "
                        "positions and borrowing capabilities.",
            industry="defi",
        )
        result = self.service.diagnose(objective)
        assert result.primary_category == ObjectiveCategory.FINANCING

    def test_diagnose_ecosystem_growth(self):
        objective = BusinessObjective(
            description="We need to launch a platform utility token that powers our "
                        "entire ecosystem and creates network effects.",
            industry="blockchain",
        )
        result = self.service.diagnose(objective)
        assert result.primary_category == ObjectiveCategory.ECOSYSTEM_GROWTH

    def test_diagnose_vague_description(self):
        objective = BusinessObjective(
            description="We have a problem that needs solving urgently.",
        )
        result = self.service.diagnose(objective)
        assert result.primary_category == ObjectiveCategory.OTHER
        assert result.confidence == DiagnosisConfidence.LOW

    def test_diagnose_with_secondary_categories(self):
        objective = BusinessObjective(
            description="We need to increase revenue through customer loyalty programs "
                        "and reduce churn while improving engagement.",
            industry="retail",
        )
        result = self.service.diagnose(objective)
        assert len(result.secondary_categories) >= 0
        assert result.confidence_score > 0

    def test_diagnose_pain_points_extraction(self):
        objective = BusinessObjective(
            description="We are experiencing high fees, slow processes, and lack of "
                        "transparency in our current system. Customer churn is increasing.",
        )
        result = self.service.diagnose(objective)
        assert len(result.pain_points) > 0

    def test_diagnose_goals_extraction(self):
        objective = BusinessObjective(
            description="We want to increase revenue, grow our user base, and improve "
                        "customer retention through innovative solutions.",
        )
        result = self.service.diagnose(objective)
        assert len(result.goals) > 0
