from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TokenAmount:
    
    raw: int
    decimals: int
    token_address: str

    def __post_init__(self) -> None:
        if self.raw < 0:
            raise ValueError("TokenAmount.raw must be >= 0")
        if not (0 <= self.decimals <= 18):
            raise ValueError("TokenAmount.decimals must be in [0, 18]")

    @property
    def as_decimal(self) -> Decimal:
        return Decimal(self.raw) / Decimal(10**self.decimals)

    def __add__(self, other: "TokenAmount") -> "TokenAmount":
        if self.token_address != other.token_address or self.decimals != other.decimals:
            raise TypeError("Cannot add TokenAmounts of different tokens")
        return TokenAmount(self.raw + other.raw, self.decimals, self.token_address)

    def __repr__(self) -> str:
        return f"TokenAmount({self.as_decimal} @ {self.token_address})"
