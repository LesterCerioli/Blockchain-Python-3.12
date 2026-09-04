from abc import ABC, abstractmethod

from ..entities.unsigned_transaction import UnsignedTransaction
from ..value_objects.gas_estimate import GasEstimate


class IGasEstimator(ABC):

    @abstractmethod
    async def estimate(self, transaction: UnsignedTransaction) -> GasEstimate:
        """Simulates the transaction and returns a gas estimate including EIP-1559 fees."""
        ...

    @abstractmethod
    async def get_base_fee(self, chain_id: int) -> GasEstimate:
        """Returns current base fee and suggested priority fee for the given chain."""
        ...

    @abstractmethod
    async def get_max_priority_fee_wei(self, chain_id: int) -> int:
        """Returns the suggested maxPriorityFeePerGas in wei (EIP-1559)."""
        ...
