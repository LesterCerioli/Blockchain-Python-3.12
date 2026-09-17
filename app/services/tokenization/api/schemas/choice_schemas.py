from pydantic import BaseModel, Field

from ...domain.entities.business_type import BusinessType


class BusinessTypesResponse(BaseModel):
    business_types: list[dict]


class TemplatesByBusinessTypeResponse(BaseModel):
    business_type: str
    templates: list[str]
    count: int


class ReorderRequest(BaseModel):
    email: str = Field(..., min_length=3, description="User email - resolved to internal user_id in backend")
    business_type: BusinessType
    description: str = Field(..., min_length=10, max_length=2000, description="description_tokenization")


class ReorderResponse(BaseModel):
    business_type: str
    description: str
    ordered_templates: list[str]
    final_options: list[str]


class ChoiceCreateRequest(BaseModel):
    email: str = Field(..., min_length=3, description="User email - resolved to internal user_id in backend")
    business_type: BusinessType
    description_tokenization: str = Field(..., min_length=10, max_length=2000)
    tokenization_template: str = Field(..., min_length=1, description="Chosen template name or 'Nenhuma destas — Criar do Zero'")


class ChoiceResponse(BaseModel):
    id: str
    user_id: str
    business_type: str
    description_tokenization: str
    tokenization_template: str
    chosen_at: str


class ChoiceListResponse(BaseModel):
    items: list[ChoiceResponse]
    total: int
