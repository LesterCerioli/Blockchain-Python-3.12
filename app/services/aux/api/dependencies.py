from __future__ import annotations

from app.services.aux.application.services import (
    AuditService,
    KycService,
    MetadataService,
    OhlcvCandleService,
    PositionService,
    RateLimitService,
    SessionService,
    TokenMetaService,
    UserService,
)


def get_session_service() -> SessionService:
    return SessionService()


def get_kyc_service() -> KycService:
    return KycService()


def get_metadata_service() -> MetadataService:
    return MetadataService()


def get_audit_service() -> AuditService:
    return AuditService()


def get_rate_limit_service() -> RateLimitService:
    return RateLimitService()


def get_token_meta_service() -> TokenMetaService:
    return TokenMetaService()


def get_user_service() -> UserService:
    return UserService()


def get_ohlcv_service() -> OhlcvCandleService:
    return OhlcvCandleService()


def get_position_service() -> PositionService:
    return PositionService()
