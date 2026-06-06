
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.defi.api.dependencies import get_chain_config_service
from app.services.defi.api.routers.chains_router import chains_router
from app.services.defi.application.chain_config_service import ChainConfigService
from app.services.defi.infrastructure.config.settings import DeFiSettings

MAINNET_IDS = [1, 137, 42161, 8453]
TESTNET_IDS = [11155111, 80001]
ALL_CHAIN_IDS = MAINNET_IDS + TESTNET_IDS


def _make_client() -> TestClient:
    app = FastAPI()
    settings = DeFiSettings()
    service = ChainConfigService(settings)
    app.dependency_overrides[get_chain_config_service] = lambda: service
    app.include_router(chains_router)
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /chains
# ---------------------------------------------------------------------------

class TestListChainsEndpoint:
    def setup_method(self):
        self.client = _make_client()

    def test_returns_200(self):
        response = self.client.get("/chains")
        assert response.status_code == 200

    def test_returns_six_chains_by_default(self):
        data = self.client.get("/chains").json()
        assert len(data) == 6

    def test_response_items_have_required_fields(self):
        data = self.client.get("/chains").json()
        for item in data:
            assert "chain_id" in item
            assert "name" in item
            assert "explorer" in item
            assert "is_testnet" in item

    def test_rpc_url_not_in_response(self):
        body = self.client.get("/chains").text
        assert "rpc_url" not in body
        assert "llamarpc" not in body
        assert "llamarpc.com" not in body

    def test_filter_testnet_true_returns_only_testnets(self):
        data = self.client.get("/chains?testnet=true").json()
        assert all(item["is_testnet"] is True for item in data)
        assert len(data) == 2

    def test_filter_testnet_false_returns_only_mainnets(self):
        data = self.client.get("/chains?testnet=false").json()
        assert all(item["is_testnet"] is False for item in data)
        assert len(data) == 4

    @pytest.mark.parametrize("chain_id", ALL_CHAIN_IDS)
    def test_all_chain_ids_present_in_default_response(self, chain_id: int):
        data = self.client.get("/chains").json()
        ids = [item["chain_id"] for item in data]
        assert chain_id in ids

    def test_mainnet_ids_present_when_filtered(self):
        data = self.client.get("/chains?testnet=false").json()
        ids = {item["chain_id"] for item in data}
        assert ids == set(MAINNET_IDS)

    def test_testnet_ids_present_when_filtered(self):
        data = self.client.get("/chains?testnet=true").json()
        ids = {item["chain_id"] for item in data}
        assert ids == set(TESTNET_IDS)


# ---------------------------------------------------------------------------
# GET /chains/{chain_id}
# ---------------------------------------------------------------------------

class TestGetChainEndpoint:
    def setup_method(self):
        self.client = _make_client()

    @pytest.mark.parametrize("chain_id", ALL_CHAIN_IDS)
    def test_returns_200_for_configured_chains(self, chain_id: int):
        response = self.client.get(f"/chains/{chain_id}")
        assert response.status_code == 200

    def test_ethereum_response_fields(self):
        data = self.client.get("/chains/1").json()
        assert data["chain_id"] == 1
        assert "Ethereum" in data["name"]
        assert data["is_testnet"] is False

    def test_sepolia_is_testnet(self):
        data = self.client.get("/chains/11155111").json()
        assert data["chain_id"] == 11155111
        assert data["is_testnet"] is True

    def test_mumbai_is_testnet(self):
        data = self.client.get("/chains/80001").json()
        assert data["chain_id"] == 80001
        assert data["is_testnet"] is True

    def test_returns_404_for_unknown_chain(self):
        response = self.client.get("/chains/56")
        assert response.status_code == 404

    def test_404_detail_contains_chain_id(self):
        response = self.client.get("/chains/9999")
        assert "9999" in response.json()["detail"]

    def test_rpc_url_not_in_response(self):
        body = self.client.get("/chains/1").text
        assert "rpc_url" not in body
