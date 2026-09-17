from ..infrastructure.config.settings import ChainConfig, DeFiSettings


class ChainNotFoundError(Exception):
    def __init__(self, chain_id: int) -> None:
        super().__init__(f"Chain {chain_id} is not configured")
        self.chain_id = chain_id


class ChainConfigService:
    def __init__(self, settings: DeFiSettings) -> None:
        self._chains: dict[int, ChainConfig] = settings.chains

    def list_all(self) -> list[tuple[int, ChainConfig]]:
        return sorted(self._chains.items())

    def list_mainnets(self) -> list[tuple[int, ChainConfig]]:
        return sorted((cid, cfg) for cid, cfg in self._chains.items() if not cfg.is_testnet)

    def list_testnets(self) -> list[tuple[int, ChainConfig]]:
        return sorted((cid, cfg) for cid, cfg in self._chains.items() if cfg.is_testnet)

    def get_by_id(self, chain_id: int) -> ChainConfig:
        cfg = self._chains.get(chain_id)
        if cfg is None:
            raise ChainNotFoundError(chain_id)
        return cfg

    def is_supported(self, chain_id: int) -> bool:
        return chain_id in self._chains
