from pydantic import BaseModel, Field


class ObjectiveInputRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        examples=[
            "We need to increase customer loyalty and reduce churn in our e-commerce platform. "
            "Our repeat purchase rate has dropped 15% in the last quarter."
        ],
    )
    industry: str | None = Field(
        default=None,
        examples=["retail", "fintech", "gaming"],
    )
    company_size: str | None = Field(
        default=None,
        examples=["startup", "sma", "mid_market", "enterprise"],
    )
    budget_range: str | None = Field(
        default=None,
        examples=["low", "medium", "high", "enterprise"],
    )
    timeline_months: int | None = Field(default=None, ge=1, le=60)
    existing_token: bool = Field(default=False)
    target_audience: str | None = Field(
        default=None,
        examples=["B2C consumers", "B2B partners", "developers"],
    )


class DiagnosisResponse(BaseModel):
    primary_category: str
    secondary_categories: list[str]
    confidence: str
    confidence_score: float
    keywords_found: list[dict]
    pain_points: list[str]
    goals: list[str]
    reasoning: str


class StrategyRecommendationResponse(BaseModel):
    strategy_code: str
    strategy_name: str
    description: str
    fit: str
    fit_score: float
    why_recommended: str
    expected_outcomes: list[str]
    considerations: list[str]
    prerequisites: list[str]
    estimated_complexity: str
    estimated_timeline_months: int | None


class TemplateRecommendationResponse(BaseModel):
    template_id: str
    template_name: str
    description: str
    token_standard: str
    category: str
    strategy: str
    fit: str
    fit_score: float
    why_recommended: str
    key_features: list[str]
    customization_options: list[str]
    limitations: list[str]
    is_derived: bool
    parent_template_id: str | None


class StartJourneyResponse(BaseModel):
    diagnosis: DiagnosisResponse
    strategies: list[StrategyRecommendationResponse]
    message: str


class SelectStrategyRequest(BaseModel):
    strategy_code: str = Field(
        ...,
        examples=["loyalty-tokenization"],
    )


class SelectStrategyResponse(BaseModel):
    strategy: StrategyRecommendationResponse
    templates: list[TemplateRecommendationResponse]
    message: str


class SelectTemplateRequest(BaseModel):
    template_id: str = Field(
        ...,
        examples=["tpl-loyalty-token"],
    )
    customization: dict | None = Field(
        default=None,
        description="Customization parameters for the template",
        examples=[{
            "token_name": "My Loyalty Token",
            "token_symbol": "MLT",
            "max_supply": 1000000,
            "business_rules": {
                "earn_rate": 0.02,
                "expiry_months": 6,
            },
        }],
    )


class PlanStepResponse(BaseModel):
    step_number: int
    title: str
    description: str
    estimated_duration: str | None
    dependencies: list[int]
    requires_approval: bool


class TokenizationPlanResponse(BaseModel):
    plan_id: str
    journey_status: str
    objective_description: str
    diagnosis_summary: str
    selected_strategy: str
    selected_template_name: str
    customization_summary: dict
    steps: list[PlanStepResponse]
    estimated_total_timeline: str | None
    estimated_cost_range: str | None
    risks: list[str]
    next_actions: list[str]
    requires_authorization: bool


class SelectTemplateResponse(BaseModel):
    plan: TokenizationPlanResponse
    message: str
    authorization_required: bool


class FallbackOption(BaseModel):
    action: str
    description: str
    endpoint: str


class FallbackResponse(BaseModel):
    message: str
    options: list[FallbackOption]
    diagnosis_hint: str
