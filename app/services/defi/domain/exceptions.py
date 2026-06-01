class DeFiError(Exception):
    """Base exception for all DeFi bounded-context errors."""


class TokenNotFoundError(DeFiError):
    def __init__(self, address: str, chain_id: int) -> None:
        super().__init__(f"Token not found: address={address} chain_id={chain_id}")
        self.address = address
        self.chain_id = chain_id


class PoolNotFoundError(DeFiError):
    def __init__(self, address: str) -> None:
        super().__init__(f"Pool not found: address={address}")
        self.address = address


class InsufficientLiquidityError(DeFiError):
    def __init__(self, pool_address: str) -> None:
        super().__init__(f"Insufficient liquidity in pool: {pool_address}")
        self.pool_address = pool_address


class SlippageExceededError(DeFiError):
    def __init__(self, expected_bps: int, actual_bps: int) -> None:
        super().__init__(
            f"Slippage exceeded: expected<={expected_bps} bps, got {actual_bps} bps"
        )
        self.expected_bps = expected_bps
        self.actual_bps = actual_bps


class ProtocolNotSupportedError(DeFiError):
    def __init__(self, protocol: str) -> None:
        super().__init__(f"Protocol not supported: {protocol}")
        self.protocol = protocol


class PriceUnavailableError(DeFiError):
    def __init__(self, token_address: str, chain_id: int) -> None:
        super().__init__(
            f"Price unavailable for token={token_address} chain_id={chain_id}"
        )
        self.token_address = token_address
        self.chain_id = chain_id


class PositionNotFoundError(DeFiError):
    def __init__(self, position_id: str) -> None:
        super().__init__(f"Position not found: id={position_id}")
        self.position_id = position_id
