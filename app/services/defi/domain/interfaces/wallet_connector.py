from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from ..entities.wallet_session import WalletSession
from ..value_objects.token_amount import TokenAmount


class IWalletConnector(ABC):

    @abstractmethod
    async def connect(self, wallet_address: str, chain_id: int) -> WalletSession: ...

    @abstractmethod
    async def disconnect(self, session_id: str) -> None: ...

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[WalletSession]: ...

    @abstractmethod
    async def is_connected(self, session_id: str) -> bool: ...

    @abstractmethod
    async def switch_chain(self, session_id: str, chain_id: int) -> WalletSession:
        """Switches the active chain for an existing session, returning the updated session."""
        ...

    @abstractmethod
    async def get_native_balance(self, session_id: str) -> Decimal:
        """Returns the native token balance (ETH, MATIC, …) in wei as a Decimal."""
        ...

    @abstractmethod
    async def get_token_balance(self, session_id: str, token_address: str) -> TokenAmount:
        """Returns the ERC-20 balance for the wallet bound to this session."""
        ...

    @abstractmethod
    async def get_nonce(self, session_id: str) -> int:
        """Returns the next pending nonce for the wallet bound to this session."""
        ...

    @abstractmethod
    async def list_active_sessions(self, wallet_address: str) -> list[WalletSession]:
        """Returns all live sessions for a given wallet address."""
        ...
