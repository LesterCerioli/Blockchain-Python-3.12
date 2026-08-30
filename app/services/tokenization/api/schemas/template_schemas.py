from pydantic import BaseModel, Field


class CreateTemplateRequest(BaseModel):
    name: str
    description: str
    category: str
    strategy: str
    token_standard: str
    token_model: dict | None = None
    characteristics: dict | None = None
    metadata: dict | None = None
    business_rules: list[dict] | None = None


class UpdateTemplateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    strategy: str | None = None
    token_standard: str | None = None
    token_model: dict | None = None
    characteristics: dict | None = None
    metadata: dict | None = None
    business_rules: list[dict] | None = None


class TemplateResponse(BaseModel):
    name: str
    description: str
    category: str
    strategy: str
    token_standard: str
    status: str
    version: str
    metadata: dict
    characteristics: dict
    token_model: dict
    business_rules: list[dict]
    created_at: str
    updated_at: str
    created_by: str
    approved_by: str | None
    approved_at: str | None


class TemplateListResponse(BaseModel):
    items: list[TemplateResponse]
    total: int


class TemplateSearchRequest(BaseModel):
    query: str | None = None
    category: str | None = None
    strategy: str | None = None
    token_standard: str | None = None
    status: str | None = None
    tags: list[str] | None = None
    industry: str | None = None


class ApproveTemplateRequest(BaseModel):
    approved_by: str


class BumpVersionRequest(BaseModel):
    bump_type: str = Field(default="patch", pattern="^(major|minor|patch)$")


class SeedCatalogResponse(BaseModel):
    seeded: int
    templates: list[TemplateResponse]
