from pydantic import BaseModel, Field

from .journey_enums import StrategyFit


class StrategyRecommendation(BaseModel):
    strategy_code: str
    strategy_name: str
    description: str
    fit: StrategyFit
    fit_score: float = Field(ge=0.0, le=1.0)
    why_recommended: str = Field(
        ...,
        description="Clear explanation of why this strategy fits the objective",
    )
    expected_outcomes: list[str] = Field(
        default_factory=list,
        description="Expected business outcomes",
    )
    considerations: list[str] = Field(
        default_factory=list,
        description="Things to consider before choosing this strategy",
    )
    prerequisites: list[str] = Field(
        default_factory=list,
        description="What's needed before implementing this strategy",
    )
    estimated_complexity: str = Field(
        default="medium",
        description="low, medium, high",
    )
    estimated_timeline_months: int | None = None

    model_config = {"frozen": True}
