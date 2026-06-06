
import pytest

from app.services.defi.application.chain_config_service import (
    ChainConfig,
    ChainConfigService,
    ChainNotFoundError,
)
from app.services.defi.infrastructure.config.settings import DeFiSettings

MAINNET_IDS = [1, 137, 42161, 8453]
TESTNET_IDS = [11155111, 80001]


def _make_service() -> ChainConfigService:
    return ChainConfigService(DeFiSettings())


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------

class TestListAll:
    def test_returns_all_six_chains(self):
        result = _make_service().list_all()
        assert len(result) == 6

    def test_result_is_sorted_by_chain_id(self):
        result = _make_service().list_all()
        ids = [cid for cid, _ in result]
        assert ids == sorted(ids)

    def test_returns_list_of_tuples(self):
        result = _make_service().list_all()
        for item in result:
            cid, cfg = item
            assert isinstance(cid, int)
            assert isinstance(cfg, ChainConfig)


# ---------------------------------------------------------------------------
# list_mainnets
# ---------------------------------------------------------------------------

class TestListMainnets:
    def test_returns_only_mainnets(self):
        result = _make_service().list_mainnets()
        for _, cfg in result:
            assert cfg.is_testnet is False

    def test_returns_four_mainnets(self):
        result = _make_service().list_mainnets()
        assert len(result) == 4

    def test_mainnet_ids_present(self):
        ids = {cid for cid, _ in _make_service().list_mainnets()}
        assert ids == set(MAINNET_IDS)

    def test_no_testnets_in_result(self):
        ids = {cid for cid, _ in _make_service().list_mainnets()}
        for testnet_id in TESTNET_IDS:
            assert testnet_id not in ids


# ---------------------------------------------------------------------------
# list_testnets
# ---------------------------------------------------------------------------

class TestListTestnets:
    def test_returns_only_testnets(self):
        result = _make_service().list_testnets()
        for _, cfg in result:
            assert cfg.is_testnet is True

    def test_returns_two_testnets(self):
        result = _make_service().list_testnets()
        assert len(result) == 2

    def test_testnet_ids_present(self):
        ids = {cid for cid, _ in _make_service().list_testnets()}
        assert ids == set(TESTNET_IDS)

    def test_no_mainnets_in_result(self):
        ids = {cid for cid, _ in _make_service().list_testnets()}
        for mainnet_id in MAINNET_IDS:
            assert mainnet_id not in ids


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

class TestGetById:
    @pytest.mark.parametrize("chain_id", MAINNET_IDS + TESTNET_IDS)
    def test_returns_config_for_known_chain(self, chain_id: int):
        cfg = _make_service().get_by_id(chain_id)
        assert isinstance(cfg, ChainConfig)

    def test_ethereum_config(self):
        cfg = _make_service().get_by_id(1)
        assert "Ethereum" in cfg.name
        assert cfg.is_testnet is False

    def test_sepolia_config(self):
        cfg = _make_service().get_by_id(11155111)
        assert "Sepolia" in cfg.name
        assert cfg.is_testnet is True

    def test_mumbai_config(self):
        cfg = _make_service().get_by_id(80001)
        assert "Mumbai" in cfg.name
        assert cfg.is_testnet is True

    def test_raises_chain_not_found_for_unknown_chain(self):
        with pytest.raises(ChainNotFoundError):
            _make_service().get_by_id(56)

    def test_chain_not_found_error_contains_chain_id(self):
        with pytest.raises(ChainNotFoundError) as exc_info:
            _make_service().get_by_id(9999)
        assert exc_info.value.chain_id == 9999

    def test_chain_not_found_message(self):
        with pytest.raises(ChainNotFoundError, match="9999"):
            _make_service().get_by_id(9999)


# ---------------------------------------------------------------------------
# is_supported
# ---------------------------------------------------------------------------

class TestIsSupported:
    @pytest.mark.parametrize("chain_id", MAINNET_IDS + TESTNET_IDS)
    def test_returns_true_for_configured_chains(self, chain_id: int):
        assert _make_service().is_supported(chain_id) is True

    def test_returns_false_for_bsc(self):
        assert _make_service().is_supported(56) is False

    def test_returns_false_for_avalanche(self):
        assert _make_service().is_supported(43114) is False

    def test_returns_false_for_zero(self):
        assert _make_service().is_supported(0) is False
