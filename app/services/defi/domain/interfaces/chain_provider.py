from abc import ABC, abstractmethod
from typing import Any, Optional

from ..entities.chain_info import ChainInfo


class IChainProvider(ABC):

    @abstractmethod
    async def get_block_number(self, chain_id: int) -> int:
        """Returns the latest confirmed block number."""
        ...

    @abstractmethod
    async def get_block_timestamp(self, chain_id: int, block_number: int) -> int:
        """Returns the Unix timestamp of a given block."""
        ...

    @abstractmethod
    async def get_chain_info(self, chain_id: int) -> ChainInfo: ...

    @abstractmethod
    async def is_contract(self, chain_id: int, address: str) -> bool:
        """Returns True when the address holds deployed bytecode."""
        ...

    @abstractmethod
    async def get_transaction_receipt(
        self,
        chain_id: int,
        tx_hash: str,
    ) -> Optional[dict[str, Any]]:
        """Returns the receipt dict or None if the transaction is not yet mined."""
        ...

    @abstractmethod
    async def call_view(
        self,
        chain_id: int,
        contract_address: str,
        encoded_call: str,
    ) -> str:
        """Executes an eth_call and returns the raw hex-encoded return data."""
        ...
