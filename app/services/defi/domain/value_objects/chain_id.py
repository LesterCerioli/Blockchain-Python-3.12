from dataclasses import dataclass
from functools import lru_cache


@lru_cache(maxsize=1)
def _get_valid_chain_ids() -> frozenset[int]:
    from app.services.defi.infrastructure.config.settings import DeFiSettings
    return frozenset(DeFiSettings().chains.keys())


SUPPORTED_CHAIN_IDS: frozenset[int] = _get_valid_chain_ids()

@dataclass(frozen=True)
class ChainId:
    value: int

    def __post_init__(self) -> None:
        valid = _get_valid_chain_ids()
        if self.value not in valid:
            raise ValueError(
                f"Unsupported chain_id {self.value}. "
                f"Supported chains: {sorted(valid)}"
            )

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)
