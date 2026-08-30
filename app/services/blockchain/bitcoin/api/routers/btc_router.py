from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_health_service, get_network_service
from ..schemas.health import HealthResponse, NodeHealthSchema
from ..schemas.network import NetworkResponse
from ...domain.interfaces.health_monitor import IHealthMonitor
from ...domain.interfaces.network_service import INetworkService

router = APIRouter(prefix="/v1/btc", tags=["bitcoin"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Node health with current block height",
)
async def get_health(
    health_service: IHealthMonitor = Depends(get_health_service),
) -> HealthResponse:
    node_healths = await health_service.check_health()
    current_block = await health_service.get_current_block_height()
    return HealthResponse(
        overall_healthy=any(h.is_healthy for h in node_healths),
        current_block_height=current_block,
        nodes=[
            NodeHealthSchema(
                node_name=h.node_name,
                is_healthy=h.is_healthy,
                block_height=h.block_height,
                latency_ms=h.latency_ms,
                last_error=h.last_error,
                is_stale=h.is_stale,
            )
            for h in node_healths
        ],
    )


@router.get(
    "/network",
    response_model=NetworkResponse,
    summary="Bitcoin network name, block height, and sync status",
)
async def get_network(
    network_service: INetworkService = Depends(get_network_service),
) -> NetworkResponse:
    try:
        info = await network_service.get_network_info()
        return NetworkResponse(
            network=info.network,
            block_height=info.block_height,
            is_syncing=info.is_syncing,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to reach Bitcoin node: {exc}",
        )
