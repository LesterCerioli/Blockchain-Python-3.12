from pydantic import BaseModel, Field

from .journey_enums import StrategyFit


class TemplateRecommendation(BaseModel):
    template_id: str
    template_name: str
    description: str
    token_standard: str
    category: str
    strategy: str
    fit: StrategyFit
    fit_score: float = Field(ge=0.0, le=1.0)
    why_recommended: str = Field(
        ...,
        description="Clear explanation of why this template fits",
    )
    key_features: list[str] = Field(
        default_factory=list,
        description="Key features of this template",
    )
    customization_options: list[str] = Field(
        default_factory=list,
        description="What can be customized",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Known limitations",
    )
    is_derived: bool = Field(
        default=False,
        description="Whether this is a derived/modified template",
    )
    parent_template_id: str | None = None

    model_config = {"frozen": True}
