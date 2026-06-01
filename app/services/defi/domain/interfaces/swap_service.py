from abc import ABC, abstractmethod

from ..value_objects.slippage import Slippage
from ..value_objects.token_amount import TokenAmount


class ISwapService(ABC):
    
    @abstractmethod
    async def get_quote(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: TokenAmount,
        chain_id: int,
    ) -> TokenAmount: ...

    @abstractmethod
    async def execute_swap(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: TokenAmount,
        slippage: Slippage,
        recipient: str,
        chain_id: int,
    ) -> str:
        """Returns the transaction hash of the submitted swap."""
        ...
