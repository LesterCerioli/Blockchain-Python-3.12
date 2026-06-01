from abc import ABC, abstractmethod
from typing import Optional

from ..value_objects.price import Price


class IPriceOracle(ABC):
    
    @abstractmethod
    async def get_price(
        self,
        base_token_address: str,
        quote_token_address: str,
        chain_id: int,
    ) -> Optional[Price]: ...

    @abstractmethod
    async def get_price_usd(self, token_address: str, chain_id: int) -> Optional[Price]: ...
