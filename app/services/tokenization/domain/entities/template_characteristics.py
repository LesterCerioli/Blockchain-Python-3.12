from pydantic import BaseModel, Field


class TemplateCharacteristics(BaseModel):
    target_use_case: str
    industry: str
    jurisdiction: str | None = None
    compliance_level: str = Field(default="standard")
    cross_chain: bool = False
    supported_chains: list[str] = Field(default_factory=list)
    gas_optimization: bool = False
    upgradeable: bool = False

    model_config = {"frozen": True}
