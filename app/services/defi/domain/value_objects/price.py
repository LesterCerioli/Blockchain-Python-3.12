from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Price:
    
    value: Decimal
    base_token_address: str
    quote_token_address: str
    chain_id: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Price.value must be >= 0")

    def invert(self) -> "Price":
        if self.value == 0:
            raise ValueError("Cannot invert a zero price")
        return Price(
            value=Decimal(1) / self.value,
            base_token_address=self.quote_token_address,
            quote_token_address=self.base_token_address,
            chain_id=self.chain_id,
        )
