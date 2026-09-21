class DeFiError(Exception):
    def __init__(self, message: str = "") -> None:
        super().__init__(message)

    def to_dict(self) -> dict[str, object]:
        return {"error": self.__class__.__name__, "message": str(self)}


class MarketDataError(DeFiError):
    pass


class ProviderUnavailableError(MarketDataError):
    def __init__(self, provider: str) -> None:
        super().__init__(f"Market data provider unavailable: {provider}")
        self.provider = provider

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["provider"] = self.provider
        return d


class RateLimitError(MarketDataError):
    def __init__(self, provider: str, retry_after: int | None = None) -> None:
        message = f"Rate limited by market data provider: {provider}"
        if retry_after is not None:
            message += f" (retry after {retry_after}s)"
        super().__init__(message)
        self.provider = provider
        self.retry_after = retry_after

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["provider"] = self.provider
        d["retry_after"] = self.retry_after
        return d


class IndexerLagError(MarketDataError):
    def __init__(self, lag_seconds: float) -> None:
        super().__init__(f"Indexer lagging behind by {lag_seconds} seconds")
        self.lag_seconds = lag_seconds

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["lag_seconds"] = self.lag_seconds
        return d


class WalletConnectionError(DeFiError):
    pass


class UnsupportedChainError(DeFiError):
    def __init__(self, chain_id: int, supported_chain_ids: tuple[int, ...]) -> None:
        super().__init__(
            f"Unsupported chain_id {chain_id}. "
            f"Supported chains: {sorted(supported_chain_ids)}"
        )
        self.chain_id = chain_id
        self.supported_chain_ids = sorted(supported_chain_ids)

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["chain_id"] = self.chain_id
        d["supported_chain_ids"] = self.supported_chain_ids
        return d


class InvalidAddressError(WalletConnectionError, ValueError):
    def __init__(self, address: str) -> None:
        super().__init__(f"Invalid wallet address: {address}")
        self.address = address

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["address"] = self.address
        return d


class NonCustodialViolationError(DeFiError):
    def __init__(self, violation_type: str, detail: str = "") -> None:
        message = f"Non-custodial violation: {violation_type}"
        if detail:
            message += f" ({detail})"
        super().__init__(message)
        self.violation_type = violation_type
        self.detail = detail

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["violation_type"] = self.violation_type
        d["detail"] = self.detail
        return d


class SanctionedAddressError(DeFiError):
    def __init__(self, address: str) -> None:
        super().__init__(f"Sanctioned wallet address: {address}")
        self.address = address

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["address"] = self.address
        return d


class ToUNotAcceptedError(DeFiError):
    def __init__(self, user_id: str = "") -> None:
        super().__init__("Terms of Use not accepted")
        self.user_id = user_id

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["user_id"] = self.user_id
        return d


class InvalidOHLCVIntervalError(DeFiError):
    def __init__(self, interval: str) -> None:
        super().__init__(f"Invalid OHLCV interval: {interval}")
        self.interval = interval

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["interval"] = self.interval
        return d


class OHLCVRangeExceededError(DeFiError):
    def __init__(self, message: str) -> None:
        super().__init__(message)

    def to_dict(self) -> dict[str, object]:
        return super().to_dict()


class TokenNotFoundError(DeFiError):
    def __init__(self, address: str, chain_id: int) -> None:
        super().__init__(f"Token not found: address={address} chain_id={chain_id}")
        self.address = address
        self.chain_id = chain_id

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["address"] = self.address
        d["chain_id"] = self.chain_id
        return d


class PoolNotFoundError(DeFiError):
    def __init__(self, address: str) -> None:
        super().__init__(f"Pool not found: address={address}")
        self.address = address

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["address"] = self.address
        return d


class NoPoolsForPairError(DeFiError):
    def __init__(self, token_in: str, token_out: str, chain_id: int) -> None:
        super().__init__(
            f"No pools found for pair {token_in}/{token_out} on chain {chain_id}"
        )
        self.token_in = token_in
        self.token_out = token_out
        self.chain_id = chain_id

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["token_in"] = self.token_in
        d["token_out"] = self.token_out
        d["chain_id"] = self.chain_id
        return d


class InsufficientLiquidityError(DeFiError):
    def __init__(self, pool_address: str) -> None:
        super().__init__(f"Insufficient liquidity in pool: {pool_address}")
        self.pool_address = pool_address

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["pool_address"] = self.pool_address
        return d


class SlippageExceededError(DeFiError):
    def __init__(self, expected_bps: int, actual_bps: int) -> None:
        super().__init__(
            f"Slippage exceeded: expected<={expected_bps} bps, got {actual_bps} bps"
        )
        self.expected_bps = expected_bps
        self.actual_bps = actual_bps

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["expected_bps"] = self.expected_bps
        d["actual_bps"] = self.actual_bps
        return d


class ProtocolNotSupportedError(DeFiError):
    def __init__(self, protocol: str) -> None:
        super().__init__(f"Protocol not supported: {protocol}")
        self.protocol = protocol

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["protocol"] = self.protocol
        return d


class PriceUnavailableError(DeFiError):
    def __init__(self, token_address: str, chain_id: int) -> None:
        super().__init__(f"Price unavailable for token: {token_address}")
        self.token_address = token_address
        self.chain_id = chain_id

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["token_address"] = self.token_address
        d["chain_id"] = self.chain_id
        return d


class PositionNotFoundError(DeFiError):
    def __init__(self, position_id: str) -> None:
        super().__init__(f"Position not found: id={position_id}")
        self.position_id = position_id

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["position_id"] = self.position_id
        return d


class IndexNotFoundError(DeFiError):
    def __init__(self, code: str) -> None:
        super().__init__(f"Index not found: code={code}")
        self.code = code

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        d["code"] = self.code
        return d
