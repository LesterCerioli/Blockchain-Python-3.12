from pydantic import BaseModel, Field

from .journey_enums import DiagnosisConfidence, ObjectiveCategory


class DiagnosisKeyword(BaseModel):
    keyword: str
    weight: float = Field(ge=0.0, le=1.0)
    context: str | None = None


class Diagnosis(BaseModel):
    primary_category: ObjectiveCategory
    secondary_categories: list[ObjectiveCategory] = Field(default_factory=list)
    confidence: DiagnosisConfidence
    confidence_score: float = Field(ge=0.0, le=1.0)
    keywords_found: list[DiagnosisKeyword] = Field(default_factory=list)
    pain_points: list[str] = Field(
        default_factory=list,
        description="Identified business pain points",
    )
    goals: list[str] = Field(
        default_factory=list,
        description="Identified business goals",
    )
    reasoning: str = Field(
        ...,
        description="Explanation of why this classification was chosen",
    )

    model_config = {"frozen": True}
