from decimal import Decimal
from typing import Optional

from web3 import AsyncWeb3

from ....domain.entities.unsigned_transaction import UnsignedTransaction
from ....domain.interfaces.gas_estimator import IGasEstimator
from ....domain.value_objects.gas_estimate import GasEstimate


class Web3GasEstimatorAdapter(IGasEstimator):
    """Outbound adapter — estimates gas and fetches fee data via web3.py."""

    def __init__(self, web3_clients: dict[int, AsyncWeb3]) -> None:
        self._clients = web3_clients

    
    async def estimate(self, transaction: UnsignedTransaction) -> GasEstimate:
        w3 = self._client(transaction.chain_id)
        tx_params = {
            "from": AsyncWeb3.to_checksum_address(transaction.from_address),
            "to": AsyncWeb3.to_checksum_address(transaction.to),
            "value": int(transaction.value),
            "data": transaction.data,
        }
        gas_limit: int = await w3.eth.estimate_gas(tx_params)
        fee_data = await self._fee_data(w3)
        return GasEstimate(
            gas_limit=gas_limit,
            gas_price_wei=fee_data["gas_price"],
            max_fee_per_gas_wei=fee_data.get("max_fee"),
            max_priority_fee_per_gas_wei=fee_data.get("max_priority_fee"),
            chain_id=transaction.chain_id,
        )

    async def get_base_fee(self, chain_id: int) -> GasEstimate:
        w3 = self._client(chain_id)
        fee_data = await self._fee_data(w3)
        return GasEstimate(
            gas_limit=21_000,  # baseline; callers should override for contract calls
            gas_price_wei=fee_data["gas_price"],
            max_fee_per_gas_wei=fee_data.get("max_fee"),
            max_priority_fee_per_gas_wei=fee_data.get("max_priority_fee"),
            chain_id=chain_id,
        )

    async def get_max_priority_fee_wei(self, chain_id: int) -> int:
        w3 = self._client(chain_id)
        try:
            return await w3.eth.max_priority_fee
        except Exception:
            return 1_500_000_000  # 1.5 gwei fallback for non-EIP-1559 chains

    
    async def _fee_data(self, w3: AsyncWeb3) -> dict:
        gas_price = await w3.eth.gas_price
        result: dict = {"gas_price": Decimal(gas_price)}
        try:
            block = await w3.eth.get_block("latest")
            base_fee = block.get("baseFeePerGas")
            if base_fee is not None:
                priority = await w3.eth.max_priority_fee
                result["max_fee"] = Decimal(base_fee * 2 + priority)
                result["max_priority_fee"] = Decimal(priority)
        except Exception:
            pass
        return result

    def _client(self, chain_id: int) -> AsyncWeb3:
        client = self._clients.get(chain_id)
        if client is None:
            raise ValueError(f"No web3 client for chain_id {chain_id}")
        return client
