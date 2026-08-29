from abc import ABC, abstractmethod

from ..value_objects.price import Price


class IPriceOracle(ABC):
    @abstractmethod
    async def get_price(
        self,
        base_token_address: str,
        quote_token_address: str,
        chain_id: int,
    ) -> Price | None: ...

    @abstractmethod
    async def get_price_usd(
        self, token_address: str, chain_id: int
    ) -> Price | None: ...
