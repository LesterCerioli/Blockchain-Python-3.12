from typing import TYPE_CHECKING

from app.services.defi.domain.interfaces.price_oracle import IPriceOracle
from app.services.defi.domain.value_objects.price import Price

if TYPE_CHECKING:
    ...


class InMemoryPriceOracle(IPriceOracle):
    def __init__(self) -> None:
        self._prices: dict[tuple[str, str, int], Price] = {}

    async def get_price(
        self,
        base_token_address: str,
        quote_token_address: str,
        chain_id: int,
    ) -> Price | None:
        key = (base_token_address.lower(), quote_token_address.lower(), chain_id)
        return self._prices.get(key)

    async def get_price_usd(self, token_address: str, chain_id: int) -> Price | None:
        key = (token_address.lower(), chain_id)
        return self._prices.get(key)

    def set_price(self, price: Price) -> None:
        key = (
            price.base_token_address.lower(),
            price.quote_token_address.lower(),
            price.chain_id,
        )
        self._prices[key] = price
