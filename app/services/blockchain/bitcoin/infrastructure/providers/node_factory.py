from .base_provider import NodeConfig
from .rpc_provider import RpcProvider


class NodeFactory:

    @staticmethod
    def create_from_config(nodes_config: list[dict]) -> list[RpcProvider]:
        providers = []
        for cfg in nodes_config:
            config = NodeConfig(
                name=cfg["name"],
                url=cfg["url"],
                rpc_user=cfg["rpc_user"],
                rpc_password=cfg["rpc_password"],
                priority=int(cfg.get("priority", 1)),
                request_timeout=float(cfg.get("request_timeout", 10.0)),
                circuit_breaker_failure_threshold=int(
                    cfg.get("circuit_breaker_failure_threshold", 5)
                ),
                circuit_breaker_recovery_seconds=int(
                    cfg.get("circuit_breaker_recovery_seconds", 60)
                ),
            )
            providers.append(RpcProvider(config))
        return providers
