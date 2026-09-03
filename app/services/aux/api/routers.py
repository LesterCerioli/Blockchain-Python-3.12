from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.services.auth.api.dependencies import get_current_token
from app.services.aux.api.dependencies import (
    get_audit_service,
    get_kyc_service,
    get_metadata_service,
    get_ohlcv_service,
    get_position_service,
    get_rate_limit_service,
    get_session_service,
    get_token_meta_service,
    get_user_service,
)
from app.services.aux.api.schemas import (
    AuditCreate,
    KycCreate,
    MetadataCreate,
    OhlcvCreate,
    PositionCreate,
    SessionCreate,
    TokenMetaUpsert,
    UserCreate,
    UserStatusUpdate,
    item_to_dict,
)

router = APIRouter(prefix="/v1")


def _bad_request(exc: ValueError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
    )


def _not_found(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))



@router.post("/sessions", tags=["Sessions"])
def create_session(
    body: SessionCreate,
    service=Depends(get_session_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    try:
        service.create(
            email=body.email,
            ip_address=body.ip_address,
            user_agent=body.user_agent,
            max_duration_ms=body.max_duration_ms or 8 * 60 * 60 * 1000,
        )
    except ValueError as exc:
        raise _bad_request(exc)
    return {"active": True}


@router.get("/sessions", tags=["Sessions"])
def get_session(
    email: str = Query(...),
    service=Depends(get_session_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    item = service.get_by_email(email)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="session not found"
        )
    data = item_to_dict(item)
    data["active"] = service.is_active_by_email(email)
    return data


@router.post("/sessions/refresh", tags=["Sessions"])
def refresh_session(
    email: str = Query(...),
    service=Depends(get_session_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    try:
        service.refresh_by_email(email)
    except ValueError as exc:
        raise _not_found(exc)
    return {"active": True}


@router.delete("/sessions", tags=["Sessions"])
def delete_session(
    email: str = Query(...),
    service=Depends(get_session_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    try:
        service.delete_by_email(email)
    except ValueError as exc:
        raise _not_found(exc)
    return {"deleted": True}



@router.post("/users", tags=["Users"])
def create_user(
    body: UserCreate,
    service=Depends(get_user_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    try:
        service.create(
            wallet_address=body.wallet_address,
            email=body.email,
            full_name=body.full_name,
            password_hash=body.password_hash,
            status=body.status,
        )
    except ValueError as exc:
        raise _bad_request(exc)
    return {
        "wallet_address": body.wallet_address.strip().lower(),
        "status": body.status,
    }


@router.get("/users", tags=["Users"])
def get_user(
    email: str = Query(...),
    service=Depends(get_user_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    item = service.get_by_email(email)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )
    return item_to_dict(item)


@router.post("/users/status", tags=["Users"])
def update_user_status(
    email: str = Query(...),
    body: UserStatusUpdate = ...,
    service=Depends(get_user_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    try:
        service.update_status(email=email, status=body.status)
    except ValueError as exc:
        if "not found" in str(exc):
            raise _not_found(exc)
        raise _bad_request(exc)
    return {"email": email, "status": body.status}



@router.post("/kyc", tags=["KYC"])
def create_kyc(
    body: KycCreate,
    service=Depends(get_kyc_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    try:
        service.create(
            email=body.email,
            full_name=body.full_name,
            verification_level=body.verification_level,
            identity_document=body.identity_document,
            document_path=body.document_path,
            attached_documents=body.attached_documents,
        )
    except ValueError as exc:
        raise _bad_request(exc)
    return {"email": body.email, "version": 1}


@router.post("/kyc/version", tags=["KYC"])
def increment_kyc_version(
    email: str = Query(...),
    body: KycCreate = ...,
    service=Depends(get_kyc_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    try:
        service.increment_version(
            email=email,
            full_name=body.full_name,
            verification_level=body.verification_level,
            identity_document=body.identity_document,
            document_path=body.document_path,
            attached_documents=body.attached_documents,
        )
    except ValueError as exc:
        if "not found" in str(exc):
            raise _not_found(exc)
        raise _bad_request(exc)
    return {"email": email, "incremented": True}


@router.get("/kyc", tags=["KYC"])
def list_kyc(
    email: str = Query(...),
    service=Depends(get_kyc_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> list[dict]:
    try:
        items = service.get_by_email(email)
    except ValueError as exc:
        if "not found" in str(exc):
            raise _not_found(exc)
        raise _bad_request(exc)
    return [item_to_dict(i) for i in items]



@router.post("/metadata", tags=["Metadata"])
def create_metadata(
    body: MetadataCreate,
    service=Depends(get_metadata_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    try:
        service.create(
            email=body.email,
            metadata_key=body.metadata_key,
            metadata_value=body.metadata_value,
        )
    except ValueError as exc:
        raise _bad_request(exc)
    return {"email": body.email}


@router.get("/metadata", tags=["Metadata"])
def list_metadata(
    email: str = Query(...),
    service=Depends(get_metadata_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> list[dict]:
    try:
        items = service.get_by_email(email)
    except ValueError as exc:
        if "not found" in str(exc):
            raise _not_found(exc)
        raise _bad_request(exc)
    return [item_to_dict(i) for i in items]


@router.post("/audit", tags=["Audit"])
def create_audit(
    body: AuditCreate,
    service=Depends(get_audit_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    try:
        service.create(
            email=body.email,
            action=body.action,
            resource=body.resource,
            details=body.details,
        )
    except ValueError as exc:
        raise _bad_request(exc)
    return {"email": body.email}


@router.get("/audit", tags=["Audit"])
def list_audit(
    email: str | None = Query(None),
    action: str | None = Query(None),
    service=Depends(get_audit_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> list[dict]:
    if action:
        items = service.get_by_action(action)
    elif email:
        try:
            items = service.get_by_email(email)
        except ValueError as exc:
            if "not found" in str(exc):
                raise _not_found(exc)
            raise _bad_request(exc)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="provide email or action query parameter",
        )
    return [item_to_dict(i) for i in items]


@router.post("/rate-limits/increment", tags=["Rate Limits"])
def increment_rate_limit(
    key: str = Query(...),
    time_window_ms: int = Query(60_000),
    service=Depends(get_rate_limit_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    count = service.increment(key=key, time_window_ms=time_window_ms)
    return {"key": key, "count": count}


@router.get("/rate-limits", tags=["Rate Limits"])
def get_rate_limit(
    key: str = Query(...),
    service=Depends(get_rate_limit_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> list[dict]:
    return [item_to_dict(i) for i in service.get(key)]


@router.post("/token-meta", tags=["Token Meta"])
def upsert_token_meta(
    body: TokenMetaUpsert,
    service=Depends(get_token_meta_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    try:
        service.upsert(
            symbol=body.symbol,
            volume_24h=body.volume_24h,
            max_price_24h=body.max_price_24h,
            min_price_24h=body.min_price_24h,
            current_price=body.current_price,
            last_check=body.last_check,
        )
    except ValueError as exc:
        raise _bad_request(exc)
    return {"symbol": body.symbol}


@router.get("/token-meta", tags=["Token Meta"])
def list_token_meta(
    symbol: str = Query(...),
    service=Depends(get_token_meta_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> list[dict]:
    return [item_to_dict(i) for i in service.get_by_symbol(symbol)]


@router.post("/ohlcv", tags=["OHLCV"])
def create_ohlcv(
    body: OhlcvCreate,
    service=Depends(get_ohlcv_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    try:
        service.insert(
            symbol=body.symbol,
            interval=body.interval,
            open_time=body.open_time,
            open_price=body.open_price,
            high=body.high,
            low=body.low,
            close=body.close,
            volume=body.volume,
        )
    except ValueError as exc:
        raise _bad_request(exc)
    return {"symbol": body.symbol, "interval": body.interval}


@router.get("/ohlcv", tags=["OHLCV"])
def list_ohlcv(
    symbol: str = Query(...),
    interval: str | None = Query(None),
    from_ms: int | None = Query(None),
    to_ms: int | None = Query(None),
    service=Depends(get_ohlcv_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> list[dict]:
    if from_ms is not None and to_ms is not None:
        items = service.get_by_symbol_time_range(symbol, from_ms, to_ms)
    elif interval:
        items = service.get_by_symbol_interval(symbol, interval)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="provide interval, or from_ms and to_ms",
        )
    return [item_to_dict(i) for i in items]


@router.post("/positions", tags=["Positions"])
def create_position(
    body: PositionCreate,
    service=Depends(get_position_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> dict:
    try:
        service.insert(
            email=body.email,
            pool_address=body.pool_address,
            token0=body.token0,
            token1=body.token1,
            liquidity=body.liquidity,
            balance=body.balance,
        )
    except ValueError as exc:
        raise _bad_request(exc)
    return {"email": body.email, "pool_address": body.pool_address}


@router.get("/positions", tags=["Positions"])
def list_positions(
    email: str | None = Query(None),
    pool_address: str | None = Query(None),
    service=Depends(get_position_service),  # noqa: B008
    payload: dict = Depends(get_current_token),
) -> list[dict]:
    if email:
        try:
            items = service.get_by_email(email)
        except ValueError as exc:
            if "not found" in str(exc):
                raise _not_found(exc)
            raise _bad_request(exc)
    elif pool_address:
        items = service.get_by_pool(pool_address)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="provide email or pool_address query parameter",
        )
    return [item_to_dict(i) for i in items]
