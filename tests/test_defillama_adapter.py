import asyncio
import respx
from app.services.defi.infrastructure.market_data.defillama_adapter import DeFiLlamaAdapter


def test_get_protocols() -> None:
    with respx.mock:
        respx.get("https://api.llama.fi/protocols").respond(
            200,
            json={
                "data": [
                    {"name": "Uniswap", "symbol": "UNI", "tvl": 4_000_000_000},
                    {"name": "Aave", "symbol": "AAVE", "tvl": 2_500_000_000},
                ]
            },
        )

        adapter = DeFiLlamaAdapter()
        protocols = asyncio.run(adapter.get_protocols())
        assert len(protocols) == 2
        assert protocols[0]["name"] == "Uniswap"
        assert protocols[0]["tvl"] == 4_000_000_000
        assert protocols[1]["name"] == "Aave"
        assert protocols[1]["tvl"] == 2_500_000_000


def test_get_historical_chain_tvl() -> None:
    with respx.mock:
        respx.get("https://api.llama.fi/v2/historicalChainTvl/eth").respond(
            200,
            json={
                "data": [
                    {"timestamp": 1700000000, "tvl": 3_500_000_000},
                    {"timestamp": 1700100000, "tvl": 3_600_000_000},
                ]
            },
        )

        adapter = DeFiLlamaAdapter()
        data = asyncio.run(adapter.get_historical_chain_tvl("eth"))
        assert len(data) == 2
        assert data[0]["tvl"] == 3_500_000_000
        assert data[1]["tvl"] == 3_600_000_000