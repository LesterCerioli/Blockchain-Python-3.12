from dataclasses import dataclass

from .price import Price


@dataclass(frozen=True)
class PricePoint:
    timestamp: int  # Unix epoch (seconds)
    price: Price

    def __post_init__(self) -> None:
        if self.timestamp < 0:
            raise ValueError("PricePoint.timestamp must be >= 0")
