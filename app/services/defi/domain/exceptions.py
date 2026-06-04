from __future__ import annotations


class DeFiError(Exception):
    
    def to_dict(self) -> dict:
        data: dict = {"error": type(self).__name__, "message": str(self)}
        data.update({k: v for k, v in vars(self).items() if not k.startswith("_")})
        return data



class MarketDataError(DeFiError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ProviderUnavailableError(MarketDataError):
    def __init__(self, provider: str) -> None:
        super().__init__(f"Provider unavailable: {provider}")
        self.provider = provider


class RateLimitError(MarketDataError):
    def __init__(self, provider: str, retry_after: int | None = None) -> None:
        msg = f"Rate limit exceeded for provider: {provider}"
        if retry_after is not None:
            msg += f" (retry after {retry_after}s)"
        super().__init__(msg)
        self.provider = provider
        self.retry_after = retry_after



class WalletConnectionError(DeFiError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidAddressError(WalletConnectionError):
    def __init__(self, address: str) -> None:
        super().__init__(f"Invalid wallet address: {address!r}")
        self.address = address


class NonCustodialViolationError(DeFiError):
    def __init__(self, violation_type: str, detail: str = "") -> None:
        msg = f"Non-custodial violation [{violation_type}]"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)
        self.violation_type = violation_type
        self.detail = detail


class SanctionedAddressError(DeFiError):
    def __init__(self, address: str) -> None:
        super().__init__(f"Sanctioned address rejected: {address}")
        self.address = address


class ToUNotAcceptedError(DeFiError):
    def __init__(self, user_id: str = "") -> None:
        msg = "Terms of Use not accepted"
        if user_id:
            msg += f" by user: {user_id}"
        super().__init__(msg)
        self.user_id = user_id


class IndexerLagError(DeFiError):
    def __init__(self, lag_seconds: float) -> None:
        super().__init__(f"Indexer lag too high: {lag_seconds:.1f}s")
        self.lag_seconds = lag_seconds



class TokenNotFoundError(DeFiError):
    def __init__(self, address: str, chain_id: int) -> None:
        super().__init__(f"Token not found: address={address} chain_id={chain_id}")
        self.address = address
        self.chain_id = chain_id


class PoolNotFoundError(DeFiError):
    def __init__(self, address: str) -> None:
        super().__init__(f"Pool not found: address={address}")
        self.address = address


class NoPoolsForPairError(DeFiError):
    def __init__(self, token_in: str, token_out: str, chain_id: int) -> None:
        super().__init__(
            f"No liquidity pools found for pair {token_in}/{token_out} on chain {chain_id}"
        )
        self.token_in = token_in
        self.token_out = token_out
        self.chain_id = chain_id


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


class RateLimitError(DeFiError):
    def __init__(self, provider: str) -> None:
        super().__init__(f"Rate limit exceeded for provider: {provider}")
        self.provider = provider


class ProviderUnavailableError(DeFiError):
    def __init__(self, provider: str, status_code: int) -> None:
        super().__init__(
            f"Market data provider unavailable: {provider} (HTTP {status_code})"
        )
        self.provider = provider
        self.status_code = status_code
