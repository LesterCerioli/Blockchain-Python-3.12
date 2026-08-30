from dataclasses import dataclass
from enum import Enum


class NetworkName(str, Enum):
    MAINNET = "main"
    TESTNET = "test"
    SIGNET = "signet"
    REGTEST = "regtest"
    UNKNOWN = "unknown"


NETWORK_BLOCK_TIME: dict[NetworkName, int] = {
    NetworkName.MAINNET: 600,
    NetworkName.TESTNET: 600,
    NetworkName.SIGNET: 30,
    NetworkName.REGTEST: 2,
}


@dataclass(frozen=True)
class NetworkConfig:
    network_name: NetworkName
    block_time_seconds: int

    @classmethod
    def from_network(cls, network: str) -> "NetworkConfig":
        try:
            name = NetworkName(network)
        except ValueError:
            name = NetworkName.UNKNOWN
        return cls(
            network_name=name,
            block_time_seconds=NETWORK_BLOCK_TIME.get(name, 600),
        )
