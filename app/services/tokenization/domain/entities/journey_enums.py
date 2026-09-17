from enum import Enum


class ObjectiveCategory(str, Enum):
    REVENUE_GROWTH = "revenue_growth"
    SALES_DECLINE = "sales_decline"
    CUSTOMER_ACQUISITION = "customer_acquisition"
    CUSTOMER_ENGAGEMENT = "customer_engagement"
    CUSTOMER_LOYALTY = "customer_loyalty"
    ASSET_TOKENIZATION = "asset_tokenization"
    RIGHTS_TOKENIZATION = "rights_tokenization"
    INCENTIVE_MODEL = "incentive_model"
    COMMUNITY_BUILDING = "community_building"
    GOVERNANCE = "governance"
    FINANCING = "financing"
    ECOSYSTEM_GROWTH = "ecosystem_growth"
    BRAND_AWARENESS = "brand_awareness"
    COST_REDUCTION = "cost_reduction"
    PARTNERSHIP_ENABLEMENT = "partnership_enablement"
    OTHER = "other"


class DiagnosisConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StrategyFit(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class JourneyStatus(str, Enum):
    STARTED = "started"
    DIAGNOSED = "diagnosed"
    STRATEGIES_PRESENTED = "strategies_presented"
    TEMPLATE_SELECTED = "template_selected"
    CUSTOMIZING = "customizing"
    PLAN_READY = "plan_ready"
    PLAN_APPROVED = "plan_approved"
    COMPLETED = "completed"
