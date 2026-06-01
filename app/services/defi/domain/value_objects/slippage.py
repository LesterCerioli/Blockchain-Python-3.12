from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Slippage:
    
    bps: int

    def __post_init__(self) -> None:
        if not (0 <= self.bps <= 10_000):
            raise ValueError(f"Slippage.bps must be in [0, 10000], got {self.bps}")

    @property
    def as_percentage(self) -> Decimal:
        return Decimal(self.bps) / Decimal(10_000)

    @classmethod
    def from_percentage(cls, pct: Decimal) -> "Slippage":
        bps = int(pct * 10_000)
        return cls(bps=bps)

    def __str__(self) -> str:
        return f"{self.as_percentage:.4%}"
