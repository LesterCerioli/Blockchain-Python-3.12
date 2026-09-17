from pydantic import BaseModel, Field


class TemplateMetadata(BaseModel):
    author: str = "platform"
    license: str = "MIT"
    audit_status: str = "pending"
    audit_date: str | None = None
    audit_firm: str | None = None
    tags: list[str] = Field(default_factory=list)
    documentation_url: str | None = None
    source_url: str | None = None

    model_config = {"frozen": True}
