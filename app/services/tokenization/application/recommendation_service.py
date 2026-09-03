from __future__ import annotations

from app.services.tokenization.domain.entities.business_objective import BusinessObjective
from app.services.tokenization.domain.entities.diagnosis import Diagnosis
from app.services.tokenization.domain.entities.journey_enums import (
    ObjectiveCategory,
    StrategyFit,
)
from app.services.tokenization.domain.entities.strategy_recommendation import (
    StrategyRecommendation,
)
from app.services.tokenization.domain.entities.template import Template
from app.services.tokenization.domain.entities.template_recommendation import (
    TemplateRecommendation,
)
from app.services.tokenization.domain.entities.tokenization_plan import (
    PlanStep,
    TokenizationPlan,
)
from app.services.tokenization.domain.interfaces.template_repository import ITemplateRepository


_CATEGORY_STRATEGIES: dict[ObjectiveCategory, list[dict]] = {
    ObjectiveCategory.REVENUE_GROWTH: [
        {
            "code": "loyalty-tokenization",
            "name": "Tokenized Loyalty Program",
            "desc": "Create a token-based loyalty system that generates recurring revenue through token utility and transaction fees.",
            "fit_base": 0.9,
            "outcomes": [
                "New recurring revenue stream from token transactions",
                "Increased customer lifetime value through token incentives",
                "Reduced loyalty program operational costs",
            ],
            "considerations": [
                "Requires regulatory review for token classification",
                "Initial setup cost for smart contract deployment",
            ],
            "prerequisites": [
                "Customer database with at least 1,000 active users",
                "E-commerce or transactional platform",
            ],
            "complexity": "medium",
            "timeline": 4,
        },
        {
            "code": "ecosystem-utility",
            "name": "Platform Utility Token",
            "desc": "Launch a native utility token that creates a closed-loop economy within your platform.",
            "fit_base": 0.8,
            "outcomes": [
                "Platform fee reduction through token staking",
                "Network effects driving organic growth",
                "Token appreciation potential",
            ],
            "considerations": [
                "Requires significant user base for network effects",
                "Complex tokenomics design needed",
            ],
            "prerequisites": [
                "Established platform with active users",
                "Clear utility use cases for the token",
            ],
            "complexity": "high",
            "timeline": 6,
        },
    ],
    ObjectiveCategory.CUSTOMER_LOYALTY: [
        {
            "code": "loyalty-tokenization",
            "name": "Tokenized Loyalty Program",
            "desc": "Replace traditional points with tradeable tokens that customers actually value.",
            "fit_base": 0.95,
            "outcomes": [
                "Higher engagement than traditional loyalty programs",
                "Token holders become brand advocates",
                "Transparent and verifiable reward distribution",
            ],
            "considerations": [
                "Customer education needed for crypto-native features",
                "Regulatory compliance varies by jurisdiction",
            ],
            "prerequisites": [
                "Existing customer base",
                "Willingness to adopt blockchain infrastructure",
            ],
            "complexity": "medium",
            "timeline": 3,
        },
    ],
    ObjectiveCategory.CUSTOMER_ENGAGEMENT: [
        {
            "code": "gamified-rewards",
            "name": "Gamified Token Rewards",
            "desc": "Implement token-based gamification to drive user engagement and retention.",
            "fit_base": 0.9,
            "outcomes": [
                "Increased daily active users",
                "Higher session duration and frequency",
                "Viral growth through social features",
            ],
            "considerations": [
                "Game mechanics design is critical for success",
                "Risk of token inflation if not carefully managed",
            ],
            "prerequisites": [
                "Platform with regular user interactions",
                "Analytics infrastructure to track engagement",
            ],
            "complexity": "medium",
            "timeline": 3,
        },
        {
            "code": "social-token",
            "name": "Social Engagement Token",
            "desc": "Create a community token that rewards social participation and content creation.",
            "fit_base": 0.8,
            "outcomes": [
                "Stronger community bonds",
                "User-generated content growth",
                "Organic brand advocacy",
            ],
            "considerations": [
                "Requires active community management",
                "Content moderation considerations",
            ],
            "prerequisites": [
                "Active social community",
                "Content creation platform or social features",
            ],
            "complexity": "medium",
            "timeline": 4,
        },
    ],
    ObjectiveCategory.CUSTOMER_ACQUISITION: [
        {
            "code": "referral-incentive",
            "name": "Token Referral Program",
            "desc": "Use token incentives to create viral customer acquisition loops.",
            "fit_base": 0.9,
            "outcomes": [
                "Reduced customer acquisition cost",
                "Viral coefficient > 1 potential",
                "Quality referrals through token staking",
            ],
            "considerations": [
                "Fraud prevention mechanisms needed",
                "Token value stability important for trust",
            ],
            "prerequisites": [
                "Product-market fit achieved",
                "Infrastructure for referral tracking",
            ],
            "complexity": "low",
            "timeline": 2,
        },
        {
            "code": "airdrop-campaign",
            "name": "Strategic Airdrop Campaign",
            "desc": "Distribute tokens to target demographics to drive awareness and onboarding.",
            "fit_base": 0.75,
            "outcomes": [
                "Rapid user base growth",
                "Brand awareness in crypto community",
                "Initial token distribution",
            ],
            "considerations": [
                "Airdrop farming risk",
                "Low retention if not paired with utility",
            ],
            "prerequisites": [
                "Clear token utility defined",
                "Marketing budget for campaign",
            ],
            "complexity": "low",
            "timeline": 2,
        },
    ],
    ObjectiveCategory.ASSET_TOKENIZATION: [
        {
            "code": "asset-tokenization",
            "name": "Real-World Asset Tokenization",
            "desc": "Tokenize physical or financial assets for fractional ownership and improved liquidity.",
            "fit_base": 0.95,
            "outcomes": [
                "Fractional ownership enabling broader investor access",
                "24/7 trading and instant settlement",
                "Reduced transaction costs",
            ],
            "considerations": [
                "Legal framework varies significantly by jurisdiction",
                "Custody and insurance requirements",
                "Regulatory approval may be required",
            ],
            "prerequisites": [
                "Verified asset with clear legal ownership",
                "Legal counsel for regulatory compliance",
                "Custody solution for underlying assets",
            ],
            "complexity": "high",
            "timeline": 8,
        },
    ],
    ObjectiveCategory.RIGHTS_TOKENIZATION: [
        {
            "code": "rights-tokenization",
            "name": "Intellectual Property Tokenization",
            "desc": "Tokenize IP rights for transparent royalty distribution and fractional ownership.",
            "fit_base": 0.9,
            "outcomes": [
                "Automated royalty distribution",
                "Fractional IP ownership",
                "Transparent rights management",
            ],
            "considerations": [
                "IP valuation can be complex",
                "Legal structure for tokenized rights",
            ],
            "prerequisites": [
                "Clear IP ownership documentation",
                "Legal framework for tokenized rights",
            ],
            "complexity": "high",
            "timeline": 6,
        },
    ],
    ObjectiveCategory.INCENTIVE_MODEL: [
        {
            "code": "behavior-incentive",
            "name": "Behavioral Incentive Token",
            "desc": "Design token incentives that align specific user behaviors with business goals.",
            "fit_base": 0.9,
            "outcomes": [
                "Measurable behavior change",
                "Data-driven incentive optimization",
                "Scalable reward mechanics",
            ],
            "considerations": [
                "Requires clear metric tracking",
                "Incentive design needs iteration",
            ],
            "prerequisites": [
                "Defined target behaviors to incentivize",
                "Analytics infrastructure",
            ],
            "complexity": "medium",
            "timeline": 3,
        },
    ],
    ObjectiveCategory.COMMUNITY_BUILDING: [
        {
            "code": "community-token",
            "name": "Community Governance Token",
            "desc": "Create a token that empowers community members with governance rights and shared ownership.",
            "fit_base": 0.9,
            "outcomes": [
                "Strong community alignment",
                "Decentralized decision making",
                "Community-driven growth",
            ],
            "considerations": [
                "Governance design is critical",
                "Minimum viable decentralization",
            ],
            "prerequisites": [
                "Active community of at least 500 members",
                "Clear governance use cases",
            ],
            "complexity": "medium",
            "timeline": 4,
        },
    ],
    ObjectiveCategory.GOVERNANCE: [
        {
            "code": "governance-token",
            "name": "DAO Governance Token",
            "desc": "Implement token-weighted voting for transparent organizational governance.",
            "fit_base": 0.95,
            "outcomes": [
                "Transparent decision-making",
                "Stakeholder alignment",
                "Reduced governance overhead",
            ],
            "considerations": [
                "Voter apathy is common",
                "Plutocracy risk with token-weighted voting",
            ],
            "prerequisites": [
                "Clear governance proposals pipeline",
                "Community willingness to participate",
            ],
            "complexity": "medium",
            "timeline": 4,
        },
    ],
    ObjectiveCategory.FINANCING: [
        {
            "code": "defi-lending",
            "name": "DeFi Lending Protocol",
            "desc": "Create tokenized lending and borrowing positions for decentralized finance.",
            "fit_base": 0.9,
            "outcomes": [
                "New revenue from interest spreads",
                "Liquidity provision opportunities",
                "Protocol-owned liquidity",
            ],
            "considerations": [
                "Smart contract risk is critical",
                "Regulatory uncertainty in DeFi",
            ],
            "prerequisites": [
                "Smart contract audit budget",
                "Initial liquidity for lending pools",
            ],
            "complexity": "high",
            "timeline": 6,
        },
    ],
    ObjectiveCategory.ECOSYSTEM_GROWTH: [
        {
            "code": "ecosystem-utility",
            "name": "Ecosystem Utility Token",
            "desc": "Launch a native token that powers your entire ecosystem with fee discounts and utility.",
            "fit_base": 0.9,
            "outcomes": [
                "Network effects across ecosystem",
                "Fee revenue from token transactions",
                "Developer and partner incentives",
            ],
            "considerations": [
                "Requires large ecosystem for utility",
                "Token value must be tied to real utility",
            ],
            "prerequisites": [
                "Multi-product or multi-service ecosystem",
                "Developer/partner community",
            ],
            "complexity": "high",
            "timeline": 6,
        },
    ],
    ObjectiveCategory.SALES_DECLINE: [
        {
            "code": "loyalty-tokenization",
            "name": "Tokenized Loyalty Program",
            "desc": "Revitalize customer relationships with a token-based retention program.",
            "fit_base": 0.85,
            "outcomes": [
                "Reduced churn rate",
                "Increased repeat purchases",
                "Win-back campaign effectiveness",
            ],
            "considerations": [
                "Must address root cause of decline",
                "Token alone won't fix product issues",
            ],
            "prerequisites": [
                "Root cause analysis completed",
                "Product/service improvements planned",
            ],
            "complexity": "medium",
            "timeline": 3,
        },
    ],
    ObjectiveCategory.BRAND_AWARENESS: [
        {
            "code": "airdrop-campaign",
            "name": "Brand Awareness Airdrop",
            "desc": "Use strategic token distribution to build brand awareness in the Web3 space.",
            "fit_base": 0.8,
            "outcomes": [
                "Increased brand visibility",
                "Community growth",
                "Media coverage",
            ],
            "considerations": [
                "Must have clear follow-up engagement plan",
                "Risk of attracting only airdrop farmers",
            ],
            "prerequisites": [
                "Marketing strategy defined",
                "Landing page and onboarding flow ready",
            ],
            "complexity": "low",
            "timeline": 2,
        },
    ],
    ObjectiveCategory.COST_REDUCTION: [
        {
            "code": "process-automation",
            "name": "Token-Automated Process",
            "desc": "Use smart contracts to automate manual processes and reduce operational costs.",
            "fit_base": 0.8,
            "outcomes": [
                "Reduced manual processing costs",
                "Fewer human errors",
                "Faster settlement times",
            ],
            "considerations": [
                "Process must be suitable for automation",
                "Initial development investment",
            ],
            "prerequisites": [
                "Clear process documentation",
                "Identified automation candidates",
            ],
            "complexity": "medium",
            "timeline": 4,
        },
    ],
    ObjectiveCategory.PARTNERSHIP_ENABLEMENT: [
        {
            "code": "partnership-token",
            "name": "Partnership Enablement Token",
            "desc": "Create tokens that facilitate partner onboarding, incentives, and revenue sharing.",
            "fit_base": 0.85,
            "outcomes": [
                "Faster partner onboarding",
                "Automated revenue sharing",
                "Aligned partner incentives",
            ],
            "considerations": [
                "Partner buy-in required",
                "Revenue sharing model must be fair",
            ],
            "prerequisites": [
                "Partner program defined",
                "Revenue sharing terms agreed",
            ],
            "complexity": "medium",
            "timeline": 4,
        },
    ],
}


class RecommendationService:
    """Maps diagnoses to strategy recommendations and template matches."""

    def __init__(self, template_repository: ITemplateRepository) -> None:
        self._repository = template_repository

    async def recommend_strategies(
        self,
        objective: BusinessObjective,
        diagnosis: Diagnosis,
    ) -> list[StrategyRecommendation]:
        strategies = _CATEGORY_STRATEGIES.get(diagnosis.primary_category, [])
        if not strategies:
            return []

        recommendations = []
        for strat in strategies:
            fit_score = strat["fit_base"]
            if objective.industry:
                fit_score = min(fit_score + 0.05, 1.0)
            if objective.company_size == "enterprise":
                fit_score = min(fit_score + 0.03, 1.0)

            fit = self._score_to_fit(fit_score)
            recommendations.append(StrategyRecommendation(
                strategy_code=strat["code"],
                strategy_name=strat["name"],
                description=strat["desc"],
                fit=fit,
                fit_score=round(fit_score, 3),
                why_recommended=self._build_strategy_reasoning(
                    strat, diagnosis, objective,
                ),
                expected_outcomes=strat["outcomes"],
                considerations=strat["considerations"],
                prerequisites=strat["prerequisites"],
                estimated_complexity=strat["complexity"],
                estimated_timeline_months=strat["timeline"],
            ))

        recommendations.sort(key=lambda r: r.fit_score, reverse=True)
        return recommendations

    async def recommend_templates(
        self,
        objective: BusinessObjective,
        diagnosis: Diagnosis,
        strategy: StrategyRecommendation,
    ) -> list[TemplateRecommendation]:
        all_templates = await self._repository.list_all(user_id="system")
        if not all_templates:
            return []

        scored = []
        for template in all_templates:
            score = self._score_template(template, diagnosis, strategy, objective)
            if score > 0.2:
                scored.append((template, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        recommendations = []
        for template, score in scored[:5]:
            fit = self._score_to_fit(score)
            recommendations.append(TemplateRecommendation(
                template_id=template.template_id,
                template_name=template.name,
                description=template.description,
                token_standard=template.token_standard,
                category=template.category,
                strategy=template.strategy,
                fit=fit,
                fit_score=round(score, 3),
                why_recommended=self._build_template_reasoning(
                    template, strategy, diagnosis, objective, score,
                ),
                key_features=self._extract_key_features(template),
                customization_options=self._extract_customization_options(template),
                limitations=self._extract_limitations(template),
                is_derived=template.is_derived,
                parent_template_id=template.parent_template_id,
            ))

        return recommendations

    async def create_plan(
        self,
        objective: BusinessObjective,
        diagnosis: Diagnosis,
        strategy: StrategyRecommendation,
        template: TemplateRecommendation,
        customization: dict | None = None,
    ) -> TokenizationPlan:
        plan_id = f"plan-{hash(objective.description) % 100000:05d}"
        steps = self._build_steps(strategy, template, customization)

        return TokenizationPlan(
            plan_id=plan_id,
            journey_status="plan_ready",
            objective_description=objective.description,
            diagnosis_summary=diagnosis.reasoning,
            selected_strategy=strategy.strategy_name,
            selected_template_name=template.template_name,
            customization_summary=customization or {},
            steps=steps,
            estimated_total_timeline=f"{strategy.estimated_timeline_months} months",
            estimated_cost_range=self._estimate_cost(strategy, template),
            risks=self._identify_risks(strategy, template, objective),
            next_actions=self._define_next_actions(strategy, template),
            requires_authorization=True,
        )

    def _score_to_fit(self, score: float) -> StrategyFit:
        if score >= 0.85:
            return StrategyFit.EXCELLENT
        elif score >= 0.7:
            return StrategyFit.GOOD
        elif score >= 0.5:
            return StrategyFit.FAIR
        return StrategyFit.POOR

    def _score_template(
        self,
        template: Template,
        diagnosis: Diagnosis,
        strategy: StrategyRecommendation,
        objective: BusinessObjective,
    ) -> float:
        score = 0.0

        category_map = {
            ObjectiveCategory.CUSTOMER_LOYALTY: "loyalty",
            ObjectiveCategory.CUSTOMER_ENGAGEMENT: "reward",
            ObjectiveCategory.CUSTOMER_ACQUISITION: "incentive",
            ObjectiveCategory.ASSET_TOKENIZATION: "asset-rights",
            ObjectiveCategory.RIGHTS_TOKENIZATION: "asset-rights",
            ObjectiveCategory.INCENTIVE_MODEL: "incentive",
            ObjectiveCategory.COMMUNITY_BUILDING: "community",
            ObjectiveCategory.GOVERNANCE: "participation",
            ObjectiveCategory.FINANCING: "financing",
            ObjectiveCategory.ECOSYSTEM_GROWTH: "ecosystem",
            ObjectiveCategory.REVENUE_GROWTH: "loyalty",
            ObjectiveCategory.SALES_DECLINE: "loyalty",
            ObjectiveCategory.BRAND_AWARENESS: "community",
            ObjectiveCategory.COST_REDUCTION: "financing",
            ObjectiveCategory.PARTNERSHIP_ENABLEMENT: "ecosystem",
        }

        target_category = category_map.get(diagnosis.primary_category)
        if target_category and template.category == target_category:
            score += 0.5

        strategy_map = {
            "loyalty-tokenization": "customer-retention",
            "gamified-rewards": "engagement",
            "social-token": "community-building",
            "referral-incentive": "behavior-incentive",
            "airdrop-campaign": "community-building",
            "asset-tokenization": "asset-tokenization",
            "rights-tokenization": "asset-tokenization",
            "behavior-incentive": "behavior-incentive",
            "community-token": "community-building",
            "governance-token": "governance",
            "defi-lending": "defi-lending",
            "ecosystem-utility": "ecosystem-utility",
            "process-automation": "ecosystem-utility",
            "partnership-token": "ecosystem-utility",
        }

        target_strategy = strategy_map.get(strategy.strategy_code)
        if target_strategy and template.strategy == target_strategy:
            score += 0.3

        if objective.industry and objective.industry.lower() in [
            t.lower() for t in template.metadata.tags
        ]:
            score += 0.1

        if template.status.value == "active":
            score += 0.1

        return min(score, 1.0)

    def _build_strategy_reasoning(
        self,
        strat: dict,
        diagnosis: Diagnosis,
        objective: BusinessObjective,
    ) -> str:
        parts = [
            f"This strategy directly addresses your {diagnosis.primary_category.value.replace('_', ' ')} objective.",
        ]

        if diagnosis.pain_points:
            parts.append(
                f"It tackles key pain points like {', '.join(diagnosis.pain_points[:2])}."
            )

        if objective.industry:
            parts.append(
                f"The {objective.industry} industry has seen success with this approach."
            )

        parts.append(f"Expected timeline: {strat['timeline']} months.")

        return " ".join(parts)

    def _build_template_reasoning(
        self,
        template: Template,
        strategy: StrategyRecommendation,
        diagnosis: Diagnosis,
        objective: BusinessObjective,
        score: float,
    ) -> str:
        parts = []

        if score >= 0.8:
            parts.append(f"'{template.name}' is an excellent match for your needs.")
        elif score >= 0.6:
            parts.append(f"'{template.name}' is a good match for your needs.")
        else:
            parts.append(f"'{template.name}' could work with some customization.")

        parts.append(
            f"It implements the {strategy.strategy_name} strategy using {template.token_standard}."
        )

        if template.metadata.tags:
            parts.append(
                f"Relevant tags: {', '.join(template.metadata.tags[:4])}."
            )

        if template.business_rules:
            parts.append(
                f"Includes {len(template.business_rules)} built-in business rules."
            )

        return " ".join(parts)

    def _extract_key_features(self, template: Template) -> list[str]:
        features = []
        if template.token_model.mintable:
            features.append("Mintable tokens")
        if template.token_model.burnable:
            features.append("Burnable tokens")
        if template.token_model.max_supply:
            features.append(f"Capped supply: {template.token_model.max_supply:,}")
        if template.business_rules:
            features.append(
                f"{len(template.business_rules)} pre-configured business rules"
            )
        if template.metadata.audit_status == "audited":
            features.append("Audited template")
        features.append(f"Standard: {template.token_standard}")
        return features

    def _extract_customization_options(self, template: Template) -> list[str]:
        options = [
            "Token name and symbol",
            "Supply parameters",
            "Mint/burn permissions",
            "Business rule parameters",
        ]
        if template.token_model.max_supply is not None:
            options.append("Maximum supply cap")
        return options

    def _extract_limitations(self, template: Template) -> list[str]:
        limitations = []
        if not template.token_model.mintable:
            limitations.append("Tokens cannot be minted after deployment")
        if not template.token_model.burnable:
            limitations.append("Tokens cannot be burned")
        if template.token_model.max_supply:
            limitations.append("Fixed maximum supply")
        return limitations

    def _build_steps(
        self,
        strategy: StrategyRecommendation,
        template: TemplateRecommendation,
        customization: dict | None,
    ) -> list[PlanStep]:
        steps = [
            PlanStep(
                step_number=1,
                title="Template Selection Confirmed",
                description=f"Selected '{template.template_name}' ({template.token_standard})",
                estimated_duration="Completed",
                requires_approval=False,
            ),
            PlanStep(
                step_number=2,
                title="Legal & Compliance Review",
                description="Review token classification and regulatory requirements",
                estimated_duration="1-2 weeks",
                requires_approval=True,
            ),
            PlanStep(
                step_number=3,
                title="Token Configuration",
                description="Customize token parameters, business rules, and economics",
                estimated_duration="1 week",
                dependencies=[2],
                requires_approval=True,
            ),
            PlanStep(
                step_number=4,
                title="Smart Contract Development",
                description="Develop and test smart contracts based on template",
                estimated_duration="2-4 weeks",
                dependencies=[3],
                requires_approval=False,
            ),
            PlanStep(
                step_number=5,
                title="Security Audit",
                description="Third-party security audit of smart contracts",
                estimated_duration="2-3 weeks",
                dependencies=[4],
                requires_approval=True,
            ),
            PlanStep(
                step_number=6,
                title="Testnet Deployment",
                description="Deploy to testnet and run integration tests",
                estimated_duration="1 week",
                dependencies=[5],
                requires_approval=False,
            ),
            PlanStep(
                step_number=7,
                title="Mainnet Deployment",
                description="Deploy to mainnet and verify contracts",
                estimated_duration="1-2 days",
                dependencies=[6],
                requires_approval=True,
            ),
            PlanStep(
                step_number=8,
                title="Launch & Monitoring",
                description="Token launch with monitoring and incident response",
                estimated_duration="Ongoing",
                dependencies=[7],
                requires_approval=False,
            ),
        ]
        return steps

    def _estimate_cost(
        self,
        strategy: StrategyRecommendation,
        template: TemplateRecommendation,
    ) -> str:
        base = {
            "low": "$5,000 - $15,000",
            "medium": "$15,000 - $50,000",
            "high": "$50,000 - $150,000",
        }
        return base.get(strategy.estimated_complexity, "$15,000 - $50,000")

    def _identify_risks(
        self,
        strategy: StrategyRecommendation,
        template: TemplateRecommendation,
        objective: BusinessObjective,
    ) -> list[str]:
        risks = []
        if strategy.estimated_complexity == "high":
            risks.append("High implementation complexity may cause delays")
        if objective.budget_range in (None, "low"):
            risks.append("Budget may be insufficient for full implementation")
        if objective.timeline_months and objective.timeline_months < 3:
            risks.append("Aggressive timeline may compromise quality")
        risks.append("Regulatory landscape may change")
        risks.append("Market conditions may affect token economics")
        return risks

    def _define_next_actions(
        self,
        strategy: StrategyRecommendation,
        template: TemplateRecommendation,
    ) -> list[str]:
        actions = [
            "Review the recommended strategy and template",
            "Consult legal counsel for regulatory requirements",
            "Define detailed token economics and business rules",
            "Approve the tokenization plan to proceed",
        ]
        if strategy.estimated_complexity == "high":
            actions.insert(2, "Engage smart contract development partner")
        return actions
