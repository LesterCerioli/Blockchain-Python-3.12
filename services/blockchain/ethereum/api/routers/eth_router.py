from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_health_service, get_network_service
from ..schemas.health import HealthResponse, ProviderHealthSchema
from ..schemas.network import NetworkResponse
from ...domain.interfaces.health_monitor import IHealthMonitor
from ...domain.interfaces.network_service import INetworkService

router = APIRouter(prefix="/v1/eth", tags=["ethereum"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Provider and chain health with current block height",
)
async def get_health(
    health_service: IHealthMonitor = Depends(get_health_service),
) -> HealthResponse:
    provider_healths = await health_service.check_health()
    current_block = await health_service.get_current_block_height()
    return HealthResponse(
        overall_healthy=any(h.is_healthy for h in provider_healths),
        current_block_height=current_block,
        providers=[
            ProviderHealthSchema(
                provider_name=h.provider_name,
                is_healthy=h.is_healthy,
                block_height=h.block_height,
                latency_ms=h.latency_ms,
                last_error=h.last_error,
                is_stale=h.is_stale,
            )
            for h in provider_healths
        ],
    )


@router.get(
    "/network",
    response_model=NetworkResponse,
    summary="Chain id, network name, and sync status",
)
async def get_network(
    network_service: INetworkService = Depends(get_network_service),
) -> NetworkResponse:
    try:
        info = await network_service.get_network_info()
        return NetworkResponse(
            chain_id=info.chain_id,
            network_name=info.network_name,
            is_syncing=info.is_syncing,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to reach Ethereum node: {exc}",
        )
