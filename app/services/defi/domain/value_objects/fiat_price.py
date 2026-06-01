from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class FiatPrice:
    amount: Decimal
    currency: str  # ISO 4217 (e.g. "USD", "EUR", "BRL")

    def __post_init__(self) -> None:
        if self.amount < Decimal(0):
            raise ValueError("FiatPrice.amount must be >= 0")
        normalized = self.currency.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError(
                f"FiatPrice.currency must be a 3-letter ISO 4217 code, got {self.currency!r}"
            )
        object.__setattr__(self, "currency", normalized)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
