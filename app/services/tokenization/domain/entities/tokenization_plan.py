from pydantic import BaseModel, Field

from .journey_enums import JourneyStatus


class PlanStep(BaseModel):
    step_number: int
    title: str
    description: str
    estimated_duration: str | None = None
    dependencies: list[int] = Field(default_factory=list)
    requires_approval: bool = False


class TokenizationPlan(BaseModel):
    plan_id: str
    journey_status: JourneyStatus
    objective_description: str
    diagnosis_summary: str
    selected_strategy: str
    selected_template_name: str
    customization_summary: dict = Field(default_factory=dict)
    steps: list[PlanStep] = Field(default_factory=list)
    estimated_total_timeline: str | None = None
    estimated_cost_range: str | None = None
    risks: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    requires_authorization: bool = Field(
        default=True,
        description="Whether this plan requires authorization before execution",
    )
    authorized_by: str | None = None
    authorized_at: str | None = None

    model_config = {"frozen": True}
