from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CryptoAmount:
    raw: int       # smallest unit (e.g. wei, satoshi)
    decimals: int  # token decimal places [0, 18]

    def __post_init__(self) -> None:
        if self.raw < 0:
            raise ValueError("CryptoAmount.raw must be >= 0")
        if not (0 <= self.decimals <= 18):
            raise ValueError(
                f"CryptoAmount.decimals must be in [0, 18], got {self.decimals}"
            )

    @property
    def as_decimal(self) -> Decimal:
        return Decimal(self.raw) / Decimal(10 ** self.decimals)

    def __repr__(self) -> str:
        return f"CryptoAmount({self.as_decimal})"
