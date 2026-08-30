from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import get_chain_config_service
from ..schemas.chain_config import ChainConfigResponse
from ...application.chain_config_service import ChainConfigService, ChainNotFoundError

chains_router = APIRouter(prefix="/chains", tags=["Chains"])


@chains_router.get(
    "",
    response_model=list[ChainConfigResponse],
    summary="List all configured chains",
)
async def list_chains(
    testnet: bool | None = Query(default=None, description="Filter by testnet (true/false). Omit for all chains."),
    service: ChainConfigService = Depends(get_chain_config_service),
) -> list[ChainConfigResponse]:
    if testnet is True:
        entries = service.list_testnets()
    elif testnet is False:
        entries = service.list_mainnets()
    else:
        entries = service.list_all()

    return [
        ChainConfigResponse(chain_id=cid, name=cfg.name, explorer=cfg.explorer, is_testnet=cfg.is_testnet)
        for cid, cfg in entries
    ]


@chains_router.get(
    "/{chain_id}",
    response_model=ChainConfigResponse,
    summary="Get configuration for a specific chain",
)
async def get_chain(
    chain_id: int,
    service: ChainConfigService = Depends(get_chain_config_service),
) -> ChainConfigResponse:
    try:
        cfg = service.get_by_id(chain_id)
    except ChainNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chain {chain_id} is not configured",
        )
    return ChainConfigResponse(chain_id=chain_id, name=cfg.name, explorer=cfg.explorer, is_testnet=cfg.is_testnet)
