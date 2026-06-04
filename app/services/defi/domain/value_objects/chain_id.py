from dataclasses import dataclass

SUPPORTED_CHAIN_IDS: frozenset[int] = frozenset({
    1,      # Ethereum Mainnet
    137,    # Polygon
    42161,  # Arbitrum One
    8453,   # Base
})


@dataclass(frozen=True)
class ChainId:
    value: int

    def __post_init__(self) -> None:
        if self.value not in SUPPORTED_CHAIN_IDS:
            raise ValueError(
                f"Unsupported chain_id {self.value}. "
                f"Supported chains: {sorted(SUPPORTED_CHAIN_IDS)}"
            )

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)
