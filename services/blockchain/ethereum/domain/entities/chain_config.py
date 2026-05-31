from dataclasses import dataclass
from enum import Enum


class NetworkName(str, Enum):
    MAINNET = "mainnet"
    SEPOLIA = "sepolia"
    UNKNOWN = "unknown"


# Chain ID → network name (config-driven, not code-driven)
CHAIN_ID_TO_NETWORK: dict[int, NetworkName] = {
    1: NetworkName.MAINNET,
    11155111: NetworkName.SEPOLIA,
}

# Expected block time in seconds per chain (used for stale-block detection)
CHAIN_BLOCK_TIME: dict[int, int] = {
    1: 12,
    11155111: 12,
}


@dataclass(frozen=True)
class ChainConfig:
    chain_id: int
    network_name: NetworkName
    block_time_seconds: int

    @classmethod
    def from_chain_id(cls, chain_id: int) -> "ChainConfig":
        return cls(
            chain_id=chain_id,
            network_name=CHAIN_ID_TO_NETWORK.get(chain_id, NetworkName.UNKNOWN),
            block_time_seconds=CHAIN_BLOCK_TIME.get(chain_id, 12),
        )
