from pydantic import BaseModel, Field

from .journey_enums import ObjectiveCategory


class BusinessObjective(BaseModel):
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Natural language description of the business problem or objective",
    )
    industry: str | None = Field(
        default=None,
        description="Industry context (e.g., retail, fintech, gaming, real-estate)",
    )
    company_size: str | None = Field(
        default=None,
        description="Company size: startup, sma, mid_market, enterprise",
    )
    budget_range: str | None = Field(
        default=None,
        description="Budget range: low, medium, high, enterprise",
    )
    timeline_months: int | None = Field(
        default=None,
        ge=1,
        le=60,
        description="Desired timeline in months",
    )
    existing_token: bool = Field(
        default=False,
        description="Whether the company already has a token",
    )
    target_audience: str | None = Field(
        default=None,
        description="Target audience (e.g., B2C consumers, B2B partners, developers)",
    )

    model_config = {"frozen": True}
