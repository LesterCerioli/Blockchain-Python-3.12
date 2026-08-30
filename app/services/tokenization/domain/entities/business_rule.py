from pydantic import BaseModel, Field


class BusinessRule(BaseModel):
    rule_id: str
    name: str
    description: str
    rule_type: str
    parameters: dict[str, str | int | float | bool] = Field(default_factory=dict)

    model_config = {"frozen": True}
