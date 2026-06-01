from typing import Any

from .base_provider import ProviderConfig
from .rpc_provider import RpcProvider


class ProviderFactory:
    
    @staticmethod
    def create_from_config(providers_config: list[dict[str, Any]]) -> list[RpcProvider]:
        providers = []
        for cfg in providers_config:
            config = ProviderConfig(
                name=cfg["name"],
                url=cfg["url"],
                priority=int(cfg.get("priority", 1)),
                connection_timeout=float(cfg.get("connection_timeout", 10.0)),
                request_timeout=float(cfg.get("request_timeout", 30.0)),
                circuit_breaker_failure_threshold=int(
                    cfg.get("circuit_breaker_failure_threshold", 5)
                ),
                circuit_breaker_recovery_seconds=int(
                    cfg.get("circuit_breaker_recovery_seconds", 60)
                ),
            )
            providers.append(RpcProvider(config))
        return providers
