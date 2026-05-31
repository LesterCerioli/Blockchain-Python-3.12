import sys
import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from services.blockchain.ethereum.api.routers.eth_router import router
from services.blockchain.ethereum.domain.interfaces.health_monitor import ProviderHealth
from services.blockchain.ethereum.domain.interfaces.network_service import NetworkInfo


def _build_app(health_service, network_service) -> FastAPI:
    app = FastAPI()
    app.state.health_service = health_service
    app.state.network_service = network_service
    app.include_router(router)
    return app


def _mock_health_service(
    providers: list[ProviderHealth],
    block_height: int | None = 20_000_000,
):
    svc = MagicMock()
    svc.check_health = AsyncMock(return_value=providers)
    svc.get_current_block_height = AsyncMock(return_value=block_height)
    return svc


def _mock_network_service(info: NetworkInfo | None = None):
    svc = MagicMock()
    if info is not None:
        svc.get_network_info = AsyncMock(return_value=info)
    else:
        svc.get_network_info = AsyncMock(side_effect=RuntimeError("node unreachable"))
    return svc


class TestHealthEndpoint:
    def test_returns_200_with_healthy_provider(self):
        healths = [
            ProviderHealth(
                provider_name="primary",
                is_healthy=True,
                block_height=20_000_000,
                latency_ms=42.5,
            )
        ]
        app = _build_app(
            health_service=_mock_health_service(healths),
            network_service=_mock_network_service(
                NetworkInfo(chain_id=1, network_name="mainnet", is_syncing=False)
            ),
        )
        client = TestClient(app)

        response = client.get("/v1/eth/health")

        assert response.status_code == 200
        body = response.json()
        assert body["overall_healthy"] is True
        assert body["current_block_height"] == 20_000_000
        assert len(body["providers"]) == 1
        assert body["providers"][0]["provider_name"] == "primary"
        assert body["providers"][0]["is_healthy"] is True

    def test_returns_200_with_all_providers_down(self):
        healths = [
            ProviderHealth(
                provider_name="primary",
                is_healthy=False,
                last_error="connection refused",
            )
        ]
        app = _build_app(
            health_service=_mock_health_service(healths, block_height=None),
            network_service=_mock_network_service(
                NetworkInfo(chain_id=1, network_name="mainnet", is_syncing=False)
            ),
        )
        client = TestClient(app)

        response = client.get("/v1/eth/health")

        assert response.status_code == 200
        body = response.json()
        assert body["overall_healthy"] is False
        assert body["current_block_height"] is None

    def test_stale_flag_propagated(self):
        healths = [
            ProviderHealth(
                provider_name="primary",
                is_healthy=True,
                block_height=20_000_000,
                is_stale=True,
            )
        ]
        app = _build_app(
            health_service=_mock_health_service(healths),
            network_service=_mock_network_service(
                NetworkInfo(chain_id=1, network_name="mainnet", is_syncing=False)
            ),
        )
        client = TestClient(app)

        body = client.get("/v1/eth/health").json()
        assert body["providers"][0]["is_stale"] is True


class TestNetworkEndpoint:
    def test_returns_200_with_network_info(self):
        info = NetworkInfo(chain_id=11155111, network_name="sepolia", is_syncing=False)
        app = _build_app(
            health_service=_mock_health_service([]),
            network_service=_mock_network_service(info),
        )
        client = TestClient(app)

        response = client.get("/v1/eth/network")

        assert response.status_code == 200
        body = response.json()
        assert body["chain_id"] == 11155111
        assert body["network_name"] == "sepolia"
        assert body["is_syncing"] is False

    def test_returns_503_when_node_unreachable(self):
        app = _build_app(
            health_service=_mock_health_service([]),
            network_service=_mock_network_service(None),
        )
        client = TestClient(app)

        response = client.get("/v1/eth/network")

        assert response.status_code == 503
