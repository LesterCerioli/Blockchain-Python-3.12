from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class GasEstimate:
    gas_limit: int
    gas_price_wei: Decimal
    max_fee_per_gas_wei: Optional[Decimal]        # EIP-1559
    max_priority_fee_per_gas_wei: Optional[Decimal]  # EIP-1559
    chain_id: int

    def __post_init__(self) -> None:
        if self.gas_limit <= 0:
            raise ValueError("GasEstimate.gas_limit must be > 0")
        if self.gas_price_wei < 0:
            raise ValueError("GasEstimate.gas_price_wei must be >= 0")
        if self.max_fee_per_gas_wei is not None and self.max_fee_per_gas_wei < 0:
            raise ValueError("GasEstimate.max_fee_per_gas_wei must be >= 0")
        if self.max_priority_fee_per_gas_wei is not None and self.max_priority_fee_per_gas_wei < 0:
            raise ValueError("GasEstimate.max_priority_fee_per_gas_wei must be >= 0")

    @property
    def is_eip1559(self) -> bool:
        return self.max_fee_per_gas_wei is not None

    @property
    def effective_gas_price_wei(self) -> Decimal:
        return self.max_fee_per_gas_wei if self.max_fee_per_gas_wei is not None else self.gas_price_wei

    @property
    def estimated_cost_wei(self) -> Decimal:
        return self.effective_gas_price_wei * self.gas_limit
