from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

from .business_rule import BusinessRule
from .template_characteristics import TemplateCharacteristics
from .template_metadata import TemplateMetadata
from .template_status import TemplateStatus
from .template_version import TemplateVersion
from .token_model import TokenModel


class Template(BaseModel):
    template_id: str
    name: str
    description: str
    category: str
    strategy: str
    token_standard: str
    status: TemplateStatus = TemplateStatus.DRAFT
    version: TemplateVersion = Field(default_factory=lambda: TemplateVersion(major=1, minor=0, patch=0))
    metadata: TemplateMetadata = Field(default_factory=TemplateMetadata)
    characteristics: TemplateCharacteristics = Field(
        default_factory=lambda: TemplateCharacteristics(
            target_use_case="general", industry="general"
        )
    )
    token_model: TokenModel = Field(
        default_factory=lambda: TokenModel(standard="ERC20", name="Token", symbol="TKN")
    )
    business_rules: list[BusinessRule] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: str = "system"
    approved_by: str | None = None
    approved_at: str | None = None

    model_config = {"frozen": True}

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("template name must not be blank")
        return v.strip()

    @field_validator("category")
    @classmethod
    def category_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("category must not be blank")
        return v.strip().lower()

    @property
    def is_editable(self) -> bool:
        return self.status in {TemplateStatus.DRAFT, TemplateStatus.PENDING_REVIEW}

    @property
    def is_active(self) -> bool:
        return self.status == TemplateStatus.ACTIVE

    @property
    def is_archived(self) -> bool:
        return self.status == TemplateStatus.ARCHIVED
