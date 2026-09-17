from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


class AuthTokenRequest(BaseModel):
    client_id: str
    client_secret: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    expires_at: str


class AuthTokenValidateRequest(BaseModel):
    token: str


class AuthTokenValidateResponse(BaseModel):
    valid: bool
    client_id: str
    token_id: str
    expires_at: str


@router.post(
    "/token",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_auth_token(
    request: AuthTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.generate_token(
            client_id=request.client_id,
            client_secret=request.client_secret,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
    return AuthTokenResponse(**result)


@router.post(
    "/token/validate",
    response_model=AuthTokenValidateResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_auth_token(
    request: AuthTokenValidateRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        result = await auth_service.validate_token(jwt_token=request.token)
    except ValueError as exc:
        detail = str(exc)
        if "expired" in detail.lower():
            code = status.HTTP_401_UNAUTHORIZED
        else:
            code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=detail)
    return AuthTokenValidateResponse(**result)
