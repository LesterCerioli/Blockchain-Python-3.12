from abc import ABC, abstractmethod

from ..entities.unsigned_transaction import UnsignedTransaction
from ..value_objects.token_amount import TokenAmount


class ITransactionBuilder(ABC):

    @abstractmethod
    async def build_swap(
        self,
        from_address: str,
        token_in_address: str,
        token_out_address: str,
        amount_in: TokenAmount,
        min_amount_out: TokenAmount,
        deadline: int,
        chain_id: int,
    ) -> UnsignedTransaction: ...

    @abstractmethod
    async def build_approve(
        self,
        from_address: str,
        token_address: str,
        spender_address: str,
        amount: TokenAmount,
        chain_id: int,
    ) -> UnsignedTransaction: ...

    @abstractmethod
    async def build_add_liquidity(
        self,
        from_address: str,
        pool_address: str,
        amount0: TokenAmount,
        amount1: TokenAmount,
        min_amount0: TokenAmount,
        min_amount1: TokenAmount,
        deadline: int,
        chain_id: int,
    ) -> UnsignedTransaction: ...

    @abstractmethod
    async def build_remove_liquidity(
        self,
        from_address: str,
        pool_address: str,
        liquidity: int,
        min_amount0: TokenAmount,
        min_amount1: TokenAmount,
        deadline: int,
        chain_id: int,
    ) -> UnsignedTransaction: ...

    @abstractmethod
    async def build_wrap_eth(
        self,
        from_address: str,
        amount_wei: int,
        chain_id: int,
    ) -> UnsignedTransaction: ...

    @abstractmethod
    async def build_unwrap_weth(
        self,
        from_address: str,
        amount_wei: int,
        chain_id: int,
    ) -> UnsignedTransaction: ...
