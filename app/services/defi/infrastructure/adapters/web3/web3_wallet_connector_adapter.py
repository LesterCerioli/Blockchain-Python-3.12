import secrets
from decimal import Decimal
from typing import Optional

from web3 import AsyncWeb3

from ....domain.entities.wallet_session import WalletSession
from ....domain.interfaces.wallet_connector import IWalletConnector
from ....domain.value_objects.token_amount import TokenAmount

_ERC20_BALANCE_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class Web3WalletConnectorAdapter(IWalletConnector):
    
    def __init__(self, web3_clients: dict[int, AsyncWeb3]) -> None:
        self._clients = web3_clients
        self._sessions: dict[str, WalletSession] = {}

    
    async def connect(self, wallet_address: str, chain_id: int) -> WalletSession:
        self._require_chain(chain_id)
        session = WalletSession(
            wallet_address=wallet_address,
            session_id=secrets.token_hex(16),
            chain_id=chain_id,
        )
        self._sessions[session.session_id] = session
        return session

    async def disconnect(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def get_session(self, session_id: str) -> Optional[WalletSession]:
        return self._sessions.get(session_id)

    async def is_connected(self, session_id: str) -> bool:
        return session_id in self._sessions

    async def switch_chain(self, session_id: str, chain_id: int) -> WalletSession:
        self._require_chain(chain_id)
        session = self._require_session(session_id)
        updated = WalletSession(
            wallet_address=session.wallet_address,
            session_id=session.session_id,
            chain_id=chain_id,
        )
        self._sessions[session_id] = updated
        return updated

    async def get_native_balance(self, session_id: str) -> Decimal:
        session = self._require_session(session_id)
        w3 = self._clients[session.chain_id]
        balance_wei = await w3.eth.get_balance(
            AsyncWeb3.to_checksum_address(session.wallet_address)
        )
        return Decimal(balance_wei)

    async def get_token_balance(self, session_id: str, token_address: str) -> TokenAmount:
        session = self._require_session(session_id)
        w3 = self._clients[session.chain_id]
        contract = w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(token_address),
            abi=_ERC20_BALANCE_ABI,
        )
        raw: int = await contract.functions.balanceOf(
            AsyncWeb3.to_checksum_address(session.wallet_address)
        ).call()
        decimals: int = await contract.functions.decimals().call()
        return TokenAmount(raw=raw, decimals=decimals, token_address=token_address.lower())

    async def get_nonce(self, session_id: str) -> int:
        session = self._require_session(session_id)
        w3 = self._clients[session.chain_id]
        return await w3.eth.get_transaction_count(
            AsyncWeb3.to_checksum_address(session.wallet_address), "pending"
        )

    async def list_active_sessions(self, wallet_address: str) -> list[WalletSession]:
        normalized = wallet_address.lower()
        return [s for s in self._sessions.values() if s.wallet_address == normalized]

    
    def _require_session(self, session_id: str) -> WalletSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"No active session: {session_id}")
        return session

    def _require_chain(self, chain_id: int) -> None:
        if chain_id not in self._clients:
            raise ValueError(f"No web3 client configured for chain_id {chain_id}")
