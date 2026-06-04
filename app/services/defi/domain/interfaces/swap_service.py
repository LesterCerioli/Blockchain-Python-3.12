from abc import ABC, abstractmethod
from decimal import Decimal

from ..entities.swap_route import SwapRoute
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
    async def get_best_route(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: TokenAmount,
        chain_id: int,
    ) -> SwapRoute:
        """Returns the optimal routing path, potentially multi-hop, for a given swap."""
        ...

    @abstractmethod
    async def get_price_impact(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: TokenAmount,
        chain_id: int,
    ) -> Decimal:
        """Returns the estimated price impact as a percentage (e.g. 0.5 means 0.5%)."""
        ...

    @abstractmethod
    async def get_minimum_amount_out(
        self,
        expected_amount_out: TokenAmount,
        slippage: Slippage,
    ) -> TokenAmount:
        """Applies slippage tolerance to compute the minimum acceptable output amount."""
        ...

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
        """Submits the swap and returns the transaction hash."""
        ...
