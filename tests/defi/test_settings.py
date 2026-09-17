"""Tests for FEATURE 1.3.4 — Configuration tests (issue #52).

DoD:
- repr(DeFiSettings(coingecko_api_key="secret123")) does not contain "secret123"
- DeFiSettings with unsupported chain_id raises ValidationError
- Chain RPC URL does not appear in uvicorn.access logs
"""
import logging

import pytest
from pydantic import ValidationError

from app.services.defi.infrastructure.config.settings import DeFiSettings


class TestSecretMasking:
    def test_coingecko_api_key_not_in_repr(self):
        settings = DeFiSettings(coingecko_api_key="secret123")
        assert "secret123" not in repr(settings)

    def test_cmc_api_key_not_in_repr(self):
        settings = DeFiSettings(cmc_api_key="supersecret456")
        assert "supersecret456" not in repr(settings)

    def test_ofac_api_key_not_in_repr(self):
        settings = DeFiSettings(ofac_api_key="ofac_secret789")
        assert "ofac_secret789" not in repr(settings)

    def test_coingecko_api_key_not_in_str(self):
        settings = DeFiSettings(coingecko_api_key="secret123")
        assert "secret123" not in str(settings)


class TestUnsupportedChainIdValidation:
    def test_unsupported_chain_id_raises_validation_error(self):
        with pytest.raises(ValidationError):
            DeFiSettings(supported_chain_ids=[99999])

    def test_multiple_unsupported_chain_ids_raises_validation_error(self):
        with pytest.raises(ValidationError):
            DeFiSettings(supported_chain_ids=[1, 99999])

    def test_valid_supported_chain_ids_accepted(self):
        settings = DeFiSettings(supported_chain_ids=[1, 137])
        assert settings.supported_chain_ids == [1, 137]

    def test_all_default_chain_ids_are_valid(self):
        settings = DeFiSettings()
        for chain_id in settings.supported_chain_ids:
            assert chain_id in settings.chains


class TestRpcUrlNotInUvicornAccessLogs:
    def test_rpc_url_not_in_uvicorn_access_log(self, caplog):
        settings = DeFiSettings()
        rpc_url = settings.chains[1].rpc_url.get_secret_value()

        with caplog.at_level(logging.INFO, logger="uvicorn.access"):
            access_logger = logging.getLogger("uvicorn.access")
            access_logger.info('"%s %s HTTP/1.1" %d', "GET", "/defi/chains/1", 200)
            access_logger.info(repr(settings))

        uvicorn_records = [r for r in caplog.records if r.name == "uvicorn.access"]
        assert uvicorn_records, "expected at least one uvicorn.access log entry"
        for record in uvicorn_records:
            assert rpc_url not in record.getMessage()

    def test_all_chain_rpc_urls_not_in_uvicorn_access_log(self, caplog):
        settings = DeFiSettings()
        rpc_urls = {
            chain_id: cfg.rpc_url.get_secret_value()
            for chain_id, cfg in settings.chains.items()
        }

        with caplog.at_level(logging.INFO, logger="uvicorn.access"):
            access_logger = logging.getLogger("uvicorn.access")
            access_logger.info(repr(settings))
            access_logger.info(str(settings.chains))

        for record in caplog.records:
            if record.name == "uvicorn.access":
                msg = record.getMessage()
                for chain_id, url in rpc_urls.items():
                    assert url not in msg, (
                        f"RPC URL for chain {chain_id} leaked into uvicorn.access log"
                    )
