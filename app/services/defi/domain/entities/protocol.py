from enum import Enum

from pydantic import BaseModel, Field


class ProtocolName(str, Enum):
    UNISWAP_V2 = "uniswap_v2"
    UNISWAP_V3 = "uniswap_v3"
    AAVE_V3 = "aave_v3"
    CURVE = "curve"
    BALANCER = "balancer"
    UNKNOWN = "unknown"


class Protocol(BaseModel):
    
    name: ProtocolName
    chain_id: int = Field(gt=0)
    router_address: str
    factory_address: str

    model_config = {"frozen": True}
