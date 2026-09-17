"""Unit tests for FEATURE 1.3.2 — Multi-chain configuration (issue #50).

Covers ChainConfig model and DeFiSettings.chains defaults.
DoD:
- RPC URLs are SecretStr
- All 6 configured chains present (Ethereum, Polygon, Arbitrum, Base, Sepolia, Mumbai)
- Mainnets have is_testnet=False; testnets have is_testnet=True
"""
import pytest
from pydantic import SecretStr, ValidationError

from app.services.defi.infrastructure.config.settings import ChainConfig, DeFiSettings

MAINNET_IDS = [1, 137, 42161, 8453]
TESTNET_IDS = [11155111, 80001]
ALL_CHAIN_IDS = MAINNET_IDS + TESTNET_IDS


# ---------------------------------------------------------------------------
# ChainConfig
# ---------------------------------------------------------------------------

class TestChainConfig:
    def test_rpc_url_is_secret_str(self):
        cfg = ChainConfig(name="Test", rpc_url="https://rpc.example.com", explorer="https://example.com")
        assert isinstance(cfg.rpc_url, SecretStr)

    def test_rpc_url_hidden_in_repr(self):
        cfg = ChainConfig(name="Test", rpc_url="https://secret.rpc.example.com", explorer="https://example.com")
        assert "secret.rpc.example.com" not in repr(cfg)
        assert "secret.rpc.example.com" not in str(cfg)

    def test_rpc_url_accessible_via_get_secret_value(self):
        url = "https://rpc.example.com/token123"
        cfg = ChainConfig(name="Test", rpc_url=url, explorer="https://example.com")
        assert cfg.rpc_url.get_secret_value() == url

    def test_is_testnet_defaults_to_false(self):
        cfg = ChainConfig(name="Test", rpc_url="https://rpc.example.com", explorer="https://example.com")
        assert cfg.is_testnet is False

    def test_is_testnet_true_when_set(self):
        cfg = ChainConfig(name="Test", rpc_url="https://rpc.example.com", explorer="https://example.com", is_testnet=True)
        assert cfg.is_testnet is True

    def test_frozen_raises_on_name_mutation(self):
        cfg = ChainConfig(name="Test", rpc_url="https://rpc.example.com", explorer="https://example.com")
        with pytest.raises(Exception):
            cfg.name = "Changed"  # type: ignore[misc]

    def test_frozen_raises_on_explorer_mutation(self):
        cfg = ChainConfig(name="Test", rpc_url="https://rpc.example.com", explorer="https://example.com")
        with pytest.raises(Exception):
            cfg.explorer = "https://other.com"  # type: ignore[misc]

    def test_missing_name_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ChainConfig(rpc_url="https://rpc.example.com", explorer="https://example.com")  # type: ignore[call-arg]

    def test_missing_rpc_url_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ChainConfig(name="Test", explorer="https://example.com")  # type: ignore[call-arg]

    def test_missing_explorer_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ChainConfig(name="Test", rpc_url="https://rpc.example.com")  # type: ignore[call-arg]

    def test_equality_of_identical_configs(self):
        a = ChainConfig(name="Test", rpc_url="https://rpc.example.com", explorer="https://example.com")
        b = ChainConfig(name="Test", rpc_url="https://rpc.example.com", explorer="https://example.com")
        assert a == b

    def test_inequality_on_different_name(self):
        a = ChainConfig(name="A", rpc_url="https://rpc.example.com", explorer="https://example.com")
        b = ChainConfig(name="B", rpc_url="https://rpc.example.com", explorer="https://example.com")
        assert a != b


# ---------------------------------------------------------------------------
# DeFiSettings.chains
# ---------------------------------------------------------------------------

class TestDeFiSettingsChains:
    def setup_method(self):
        self.settings = DeFiSettings()

    def test_chains_field_exists(self):
        assert hasattr(self.settings, "chains")

    def test_chains_has_six_entries(self):
        assert len(self.settings.chains) == 6

    @pytest.mark.parametrize("chain_id", ALL_CHAIN_IDS)
    def test_all_required_chain_ids_present(self, chain_id: int):
        assert chain_id in self.settings.chains

    @pytest.mark.parametrize("chain_id", MAINNET_IDS)
    def test_mainnet_chains_are_not_testnets(self, chain_id: int):
        assert self.settings.chains[chain_id].is_testnet is False

    @pytest.mark.parametrize("chain_id", TESTNET_IDS)
    def test_testnet_chains_are_marked_as_testnet(self, chain_id: int):
        assert self.settings.chains[chain_id].is_testnet is True

    @pytest.mark.parametrize("chain_id", ALL_CHAIN_IDS)
    def test_rpc_url_is_secret_str(self, chain_id: int):
        assert isinstance(self.settings.chains[chain_id].rpc_url, SecretStr)

    @pytest.mark.parametrize("chain_id", ALL_CHAIN_IDS)
    def test_rpc_url_is_non_empty(self, chain_id: int):
        assert self.settings.chains[chain_id].rpc_url.get_secret_value().strip()

    @pytest.mark.parametrize("chain_id", ALL_CHAIN_IDS)
    def test_chain_name_is_non_empty(self, chain_id: int):
        assert self.settings.chains[chain_id].name.strip()

    @pytest.mark.parametrize("chain_id", ALL_CHAIN_IDS)
    def test_explorer_is_non_empty(self, chain_id: int):
        assert self.settings.chains[chain_id].explorer.strip()

    def test_ethereum_name(self):
        assert "Ethereum" in self.settings.chains[1].name

    def test_polygon_name(self):
        assert "Polygon" in self.settings.chains[137].name

    def test_arbitrum_name(self):
        assert "Arbitrum" in self.settings.chains[42161].name

    def test_base_name(self):
        assert "Base" in self.settings.chains[8453].name

    def test_sepolia_name(self):
        assert "Sepolia" in self.settings.chains[11155111].name

    def test_mumbai_name(self):
        assert "Mumbai" in self.settings.chains[80001].name

    def test_rpc_url_not_leaked_in_settings_repr(self):
        settings = DeFiSettings()
        rpc = settings.chains[1].rpc_url.get_secret_value()
        assert rpc not in repr(settings.chains[1])
