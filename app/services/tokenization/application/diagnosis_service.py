from __future__ import annotations

from app.services.tokenization.domain.entities.business_objective import BusinessObjective
from app.services.tokenization.domain.entities.diagnosis import Diagnosis, DiagnosisKeyword
from app.services.tokenization.domain.entities.journey_enums import (
    DiagnosisConfidence,
    ObjectiveCategory,
)


_CATEGORY_KEYWORDS: dict[ObjectiveCategory, list[tuple[str, float]]] = {
    ObjectiveCategory.REVENUE_GROWTH: [
        ("revenue", 1.0), ("income", 0.9), ("monetize", 0.9), ("profit", 0.8),
        ("sales increase", 1.0), ("upsell", 0.7), ("cross-sell", 0.7),
        ("premium", 0.6), ("subscription", 0.7), ("recurring", 0.8),
        ("mrr", 0.9), ("arr", 0.9), ("arpu", 0.9), ("ltv", 0.8),
    ],
    ObjectiveCategory.SALES_DECLINE: [
        ("sales decline", 1.0), ("revenue drop", 1.0), ("churn", 0.9),
        ("losing customers", 0.9), ("retention", 0.8), ("decreasing sales", 1.0),
        ("down trend", 0.7), ("customer loss", 0.9), ("attrition", 0.8),
    ],
    ObjectiveCategory.CUSTOMER_ACQUISITION: [
        ("acquire", 1.0), ("acquisition", 1.0), ("new customers", 1.0),
        ("user growth", 0.9), ("onboard", 0.7), ("sign up", 0.8),
        ("referral", 0.9), ("viral", 0.8), ("growth hack", 0.7),
        ("lead generation", 0.8), ("prospects", 0.7),
    ],
    ObjectiveCategory.CUSTOMER_ENGAGEMENT: [
        ("engagement", 1.0), ("active users", 0.9), ("participation", 0.9),
        ("互动", 0.8), ("gamification", 0.9), ("rewards", 0.8),
        ("stickiness", 0.8), ("session time", 0.7), ("frequency", 0.7),
        ("daily active", 0.9), ("mau", 0.8), ("dau", 0.9),
    ],
    ObjectiveCategory.CUSTOMER_LOYALTY: [
        ("loyalty", 1.0), ("retention", 0.9), ("repeat purchase", 0.9),
        ("customer lifetime", 0.8), ("clv", 0.9), ("ltv", 0.9),
        ("loyal", 0.8), ("vip", 0.7), ("tier", 0.6),
        ("points", 0.8), ("rewards program", 0.9),
    ],
    ObjectiveCategory.ASSET_TOKENIZATION: [
        ("tokenize", 1.0), ("tokenization", 1.0), ("real estate", 0.9),
        ("property", 0.7), ("asset", 0.8), ("fractional", 0.9),
        ("ownership", 0.7), ("rwa", 1.0), ("real-world", 0.9),
        ("commodit", 0.7), ("art", 0.6), ("collectible", 0.6),
    ],
    ObjectiveCategory.RIGHTS_TOKENIZATION: [
        ("intellectual property", 1.0), ("ip rights", 1.0), ("copyright", 0.9),
        ("royalt", 0.9), ("licensing", 0.8), ("patent", 0.7),
        ("content rights", 0.9), ("media rights", 0.9), ("music rights", 0.9),
        ("nft", 0.7), ("digital rights", 0.9),
    ],
    ObjectiveCategory.INCENTIVE_MODEL: [
        ("incentive", 1.0), ("referral program", 0.9), ("bonus", 0.8),
        ("reward behavior", 0.9), ("gamification", 0.7), ("target action", 0.8),
        ("badges", 0.7), ("achievements", 0.7), ("milestones", 0.6),
        ("cashback", 0.8), ("kickback", 0.7),
    ],
    ObjectiveCategory.COMMUNITY_BUILDING: [
        ("community", 1.0), ("social token", 0.9), ("creator economy", 0.8),
        ("fan token", 0.9), ("social", 0.7), ("membership", 0.8),
        ("dao", 0.7), ("collective", 0.7), ("movement", 0.6),
    ],
    ObjectiveCategory.GOVERNANCE: [
        ("governance", 1.0), ("voting", 0.9), ("decision making", 0.8),
        ("decentralized", 0.7), ("dao", 0.8), ("proposal", 0.8),
        ("stakeholder", 0.7), ("consensus", 0.7), ("transparent", 0.6),
    ],
    ObjectiveCategory.FINANCING: [
        ("financing", 1.0), ("lending", 0.9), ("borrowing", 0.9),
        ("yield", 0.8), ("defi", 0.8), ("liquidity", 0.8),
        ("capital raise", 0.9), ("fundraising", 0.8), ("ico", 0.7),
        ("ido", 0.7), ("investment", 0.7),
    ],
    ObjectiveCategory.ECOSYSTEM_GROWTH: [
        ("ecosystem", 1.0), ("platform token", 0.9), ("utility token", 0.9),
        ("network effect", 0.8), ("protocol", 0.7), ("infrastructure", 0.7),
        ("developer", 0.6), ("integration", 0.6), ("api", 0.5),
    ],
    ObjectiveCategory.BRAND_AWARENESS: [
        ("brand awareness", 1.0), ("visibility", 0.8), ("marketing", 0.7),
        ("recognition", 0.7), ("mindshare", 0.7), ("hype", 0.6),
        ("launch", 0.6), ("campaign", 0.6),
    ],
    ObjectiveCategory.COST_REDUCTION: [
        ("cost reduction", 1.0), ("efficiency", 0.8), ("automate", 0.8),
        ("streamline", 0.7), ("reduce fees", 0.9), ("intermediary", 0.7),
        ("disintermediat", 0.8), ("optimize", 0.6),
    ],
    ObjectiveCategory.PARTNERSHIP_ENABLEMENT: [
        ("partnership", 1.0), ("partner", 0.9), ("alliance", 0.8),
        ("collaboration", 0.7), ("b2b", 0.7), ("integration", 0.6),
        ("ecosystem partner", 0.8),
    ],
}

_PAIN_POINT_KEYWORDS: list[tuple[str, float]] = [
    ("high fees", 0.9), ("slow process", 0.8), ("manual", 0.7),
    ("inefficient", 0.8), ("expensive", 0.7), ("complex", 0.6),
    ("lack of transparency", 0.9), ("trust issues", 0.8),
    ("low engagement", 0.8), ("high churn", 0.9), ("declining", 0.7),
    ("losing market share", 0.8), ("stagnant", 0.7), ("outdated", 0.6),
    ("bottleneck", 0.7), ("friction", 0.7), ("barrier", 0.6),
]

_GOAL_KEYWORDS: list[tuple[str, float]] = [
    ("increase", 0.7), ("improve", 0.7), ("grow", 0.8),
    ("scale", 0.8), ("expand", 0.7), ("launch", 0.6),
    ("modernize", 0.7), ("innovate", 0.7), ("transform", 0.8),
    ("optimize", 0.6), ("retain", 0.7), ("attract", 0.7),
]


class DiagnosisService:
    
    def __init__(self, llm_adapter=None, diagnosis_repository=None, settings=None) -> None:
        self._llm = llm_adapter
        self._history_repo = diagnosis_repository
        self._settings = settings

    def diagnose(self, objective: BusinessObjective) -> Diagnosis:
        text = objective.description.lower()
        scores: dict[ObjectiveCategory, float] = {}
        keywords_found: dict[ObjectiveCategory, list[DiagnosisKeyword]] = {}

        for category, keywords in _CATEGORY_KEYWORDS.items():
            cat_score = 0.0
            cat_keywords: list[DiagnosisKeyword] = []
            for keyword, weight in keywords:
                if keyword in text:
                    cat_score += weight
                    cat_keywords.append(DiagnosisKeyword(
                        keyword=keyword,
                        weight=weight,
                        context=self._extract_context(text, keyword),
                    ))
            if cat_score > 0:
                scores[category] = cat_score
                keywords_found[category] = cat_keywords

        if not scores:
            return Diagnosis(
                primary_category=ObjectiveCategory.OTHER,
                confidence=DiagnosisConfidence.LOW,
                confidence_score=0.1,
                reasoning="No clear tokenization-related keywords found. "
                          "Please provide more details about your business objective.",
            )

        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_categories[0]
        secondary = [c for c, _ in sorted_categories[1:3]]

        max_possible = max(len(kws) for kws in _CATEGORY_KEYWORDS.values())
        confidence_score = min(primary[1] / (max_possible * 0.3), 1.0)

        if confidence_score >= 0.7:
            confidence = DiagnosisConfidence.HIGH
        elif confidence_score >= 0.4:
            confidence = DiagnosisConfidence.MEDIUM
        else:
            confidence = DiagnosisConfidence.LOW

        pain_points = self._extract_pain_points(text)
        goals = self._extract_goals(text)

        reasoning = self._build_reasoning(
            primary[0], confidence, keywords_found.get(primary[0], []),
            pain_points, goals, objective,
        )

        return Diagnosis(
            primary_category=primary[0],
            secondary_categories=secondary,
            confidence=confidence,
            confidence_score=round(confidence_score, 3),
            keywords_found=keywords_found.get(primary[0], []),
            pain_points=pain_points,
            goals=goals,
            reasoning=reasoning,
        )

    async def diagnose_with_llm(
        self,
        objective: BusinessObjective,
        user_id: str | None = None,
        tokenization_implementation_id: str | None = None,
    ) -> Diagnosis:
        
        llm_result = None
        if self._llm is not None:
            try:
                # adapters expose diagnose(description, industry)
                llm_result = await self._llm.diagnose(objective.description, objective.industry)  # type: ignore[attr-defined]
            except Exception:
                llm_result = None
        if llm_result and isinstance(llm_result, dict) and llm_result.get("primary_category"):
            try:
                cat_val = str(llm_result["primary_category"]).lower()
                primary = ObjectiveCategory(cat_val)
                conf_val = str(llm_result.get("confidence", "medium")).lower()
                confidence = DiagnosisConfidence(conf_val) if conf_val in ("high", "medium", "low") else DiagnosisConfidence.MEDIUM
                score = float(llm_result.get("confidence_score", 0.7))
                score = max(0.0, min(1.0, score))
                # persist history if repo available
                if self._history_repo is not None and user_id:
                    try:
                        await self._history_repo.save(  # type: ignore[attr-defined]
                            user_id=user_id,
                            objective_description=objective.description,
                            primary_category=primary.value,
                            diagnosis_payload=llm_result,
                            tokenization_implementation_id=tokenization_implementation_id,
                        )
                    except Exception:
                        pass
                secondary = []
                for sc in llm_result.get("secondary_categories", [])[:2]:
                    try:
                        secondary.append(ObjectiveCategory(str(sc).lower()))
                    except Exception:
                        continue
                
                text_lower = objective.description.lower()
                base_pain = self._extract_pain_points(text_lower)
                base_goals = self._extract_goals(text_lower)
                llm_pain = llm_result.get("pain_points", []) or base_pain
                llm_goals = llm_result.get("goals", []) or base_goals
                reasoning = llm_result.get("reasoning") or self._build_reasoning(
                    primary, confidence, [], llm_pain, llm_goals, objective
                )
                return Diagnosis(
                    primary_category=primary,
                    secondary_categories=secondary,
                    confidence=confidence,
                    confidence_score=round(score, 3),
                    keywords_found=[],
                    pain_points=llm_pain[:5],
                    goals=llm_goals[:5],
                    reasoning=reasoning,
                )
            except Exception:
                pass
        
        result = self.diagnose(objective)
        if self._history_repo is not None and user_id:
            try:
                await self._history_repo.save(
                    user_id=user_id,
                    objective_description=objective.description,
                    primary_category=result.primary_category.value,
                    diagnosis_payload=result.model_dump(),
                    tokenization_implementation_id=tokenization_implementation_id,
                )
            except Exception:
                pass
        return result

    def _extract_context(self, text: str, keyword: str, window: int = 50) -> str:
        idx = text.find(keyword)
        if idx == -1:
            return ""
        start = max(0, idx - window)
        end = min(len(text), idx + len(keyword) + window)
        return text[start:end].strip()

    def _extract_pain_points(self, text: str) -> list[str]:
        found = []
        for keyword, weight in _PAIN_POINT_KEYWORDS:
            if keyword in text:
                found.append(keyword)
        return found[:5]

    def _extract_goals(self, text: str) -> list[str]:
        found = []
        for keyword, weight in _GOAL_KEYWORDS:
            if keyword in text:
                found.append(keyword)
        return found[:5]

    def _build_reasoning(
        self,
        primary: ObjectiveCategory,
        confidence: DiagnosisConfidence,
        keywords: list[DiagnosisKeyword],
        pain_points: list[str],
        goals: list[str],
        objective: BusinessObjective,
    ) -> str:
        parts = [
            f"Based on the analysis of your business objective, the primary classification is "
            f"**{primary.value}** with {confidence.value} confidence.",
        ]

        if keywords:
            kw_list = ", ".join(f'"{kw.keyword}"' for kw in keywords[:5])
            parts.append(f"Key terms identified: {kw_list}.")

        if pain_points:
            parts.append(f"Pain points detected: {', '.join(pain_points)}.")

        if goals:
            parts.append(f"Goals identified: {', '.join(goals)}.")

        if objective.industry:
            parts.append(f"Industry context: {objective.industry}.")

        category_explanations = {
            ObjectiveCategory.REVENUE_GROWTH: "Token-based models can create new revenue streams through transaction fees, premium access tiers, and token appreciation.",
            ObjectiveCategory.CUSTOMER_LOYALTY: "Tokenized loyalty programs offer higher engagement, tradability, and transparent value compared to traditional point systems.",
            ObjectiveCategory.CUSTOMER_ACQUISITION: "Token incentives can accelerate user acquisition through referral bonuses, airdrops, and community-driven growth.",
            ObjectiveCategory.CUSTOMER_ENGAGEMENT: "Gamification through tokens increases user participation, retention, and platform stickiness.",
            ObjectiveCategory.ASSET_TOKENIZATION: "Fractional ownership through tokens unlocks liquidity for illiquid assets and enables broader investor participation.",
            ObjectiveCategory.RIGHTS_TOKENIZATION: "Tokenizing intellectual property enables transparent royalty distribution and fractional ownership of creative works.",
            ObjectiveCategory.INCENTIVE_MODEL: "Token incentives align user behavior with business goals through measurable, transparent reward mechanisms.",
            ObjectiveCategory.COMMUNITY_BUILDING: "Social tokens create aligned incentives between creators/brands and their communities.",
            ObjectiveCategory.GOVERNANCE: "Token-based governance enables transparent, decentralized decision-making among stakeholders.",
            ObjectiveCategory.FINANCING: "DeFi tokens enable new financing mechanisms including lending, yield generation, and capital formation.",
            ObjectiveCategory.ECOSYSTEM_GROWTH: "Platform utility tokens create network effects and align incentives across ecosystem participants.",
        }

        if primary in category_explanations:
            parts.append(category_explanations[primary])

        return " ".join(parts)
