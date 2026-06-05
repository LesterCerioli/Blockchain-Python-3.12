from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from ..dependencies import get_platform_secrets_service
from ..schemas.platform_secrets import (
    PlatformSecretCreate,
    PlatformSecretResponse,
    PlatformSecretUpdate,
)
from ...infrastructure.persistence.platform_secrets_service import PlatformSecretsService

admin_router = APIRouter(prefix="/admin/secrets", tags=["Admin — Platform Secrets"])


@admin_router.post(
    "",
    response_model=PlatformSecretResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a platform secret",
    description=(
        "Stores a new platform-level API key or secret. "
        "The value is write-only — it is never returned in any response."
    ),
)
async def create_secret(
    body: PlatformSecretCreate,
    service: PlatformSecretsService = Depends(get_platform_secrets_service),
) -> PlatformSecretResponse:
    try:
        row = await service.create(
            key_name=body.key_name,
            value_enc=body.value,
            updated_by=body.updated_by,
            description=body.description,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A secret with key_name '{body.key_name}' already exists. Use PUT to update it.",
        )
    return PlatformSecretResponse(**row)


@admin_router.get(
    "",
    response_model=list[PlatformSecretResponse],
    summary="List all platform secrets",
    description="Returns metadata for all stored secrets. Values are never included.",
)
async def list_secrets(
    service: PlatformSecretsService = Depends(get_platform_secrets_service),
) -> list[PlatformSecretResponse]:
    rows = await service.list_all()
    return [PlatformSecretResponse(**row) for row in rows]


@admin_router.get(
    "/{key_name}",
    response_model=PlatformSecretResponse,
    summary="Get a platform secret by key name",
    description="Returns metadata for a single secret. The value is never included.",
)
async def get_secret(
    key_name: str,
    service: PlatformSecretsService = Depends(get_platform_secrets_service),
) -> PlatformSecretResponse:
    row = await service.get_by_key_name(key_name)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Secret '{key_name}' not found.",
        )
    return PlatformSecretResponse(**row)


@admin_router.put(
    "/{key_name}",
    response_model=PlatformSecretResponse,
    summary="Update a platform secret",
    description=(
        "Replaces the value of an existing secret. "
        "If description is omitted the existing description is preserved."
    ),
)
async def update_secret(
    key_name: str,
    body: PlatformSecretUpdate,
    service: PlatformSecretsService = Depends(get_platform_secrets_service),
) -> PlatformSecretResponse:
    row = await service.update(
        key_name=key_name,
        value_enc=body.value,
        updated_by=body.updated_by,
        description=body.description,
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Secret '{key_name}' not found. Use POST to create it.",
        )
    return PlatformSecretResponse(**row)


@admin_router.delete(
    "/{key_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a platform secret",
)
async def delete_secret(
    key_name: str,
    service: PlatformSecretsService = Depends(get_platform_secrets_service),
) -> None:
    deleted = await service.delete(key_name)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Secret '{key_name}' not found.",
        )
