from pydantic import BaseModel, Field


class TemplateVersion(BaseModel):
    major: int = Field(ge=1)
    minor: int = Field(ge=0)
    patch: int = Field(ge=0)
    audit_report_url: str | None = None

    model_config = {"frozen": True}

    def to_string(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible_with(self, other: "TemplateVersion") -> bool:
        return self.major == other.major and self.minor <= other.minor
