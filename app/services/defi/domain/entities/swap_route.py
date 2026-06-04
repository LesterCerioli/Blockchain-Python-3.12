from dataclasses import dataclass

from pydantic import BaseModel, Field

from ..value_objects.token_amount import TokenAmount


@dataclass(frozen=True)
class SwapHop:
    pool_address: str
    token_in_address: str
    token_out_address: str
    fee_bps: int

    def __post_init__(self) -> None:
        if self.fee_bps < 0:
            raise ValueError("SwapHop.fee_bps must be >= 0")


class SwapRoute(BaseModel):
    token_in_address: str
    token_out_address: str
    amount_in: TokenAmount
    expected_amount_out: TokenAmount
    price_impact_bps: int = Field(ge=0, description="Price impact in basis points")
    hops: list[SwapHop]
    chain_id: int = Field(gt=0)

    @property
    def is_multi_hop(self) -> bool:
        return len(self.hops) > 1

    model_config = {"frozen": True, "arbitrary_types_allowed": True}
