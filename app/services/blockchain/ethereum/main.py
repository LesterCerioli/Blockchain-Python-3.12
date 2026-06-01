from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.routers.eth_router import router as eth_router
from .application.health_service import HealthService
from .application.network_service import NetworkService
from .domain.adapters.eth_chain_adapter import EthChainAdapter
from .infrastructure.config.settings import EthereumSettings
from .infrastructure.persistence.database import Database
from .infrastructure.persistence.provider_repository import PostgresProviderRepository
from .infrastructure.providers.multi_provider import MultiProvider
from .infrastructure.providers.provider_factory import ProviderFactory


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = EthereumSettings()
    db = Database(settings.database_url)
    providers = ProviderFactory.create_from_config(settings.providers)
    multi_provider = MultiProvider(providers)
    chain_adapter = EthChainAdapter(multi_provider)
    repository = PostgresProviderRepository(db)

    app.state.health_service = HealthService(
        chain_adapter=chain_adapter,
        providers=providers,
        repository=repository,
        stale_block_threshold_seconds=settings.stale_block_threshold_seconds,
    )
    app.state.network_service = NetworkService(chain_adapter)
    app.state.multi_provider = multi_provider
    app.state.db = db

    yield

    await multi_provider.close()
    await db.close()


app = FastAPI(
    title="CryptoBank — Ethereum RPC Service",
    version="1.0.0",
    description="Async multi-provider RPC client with failover, circuit breaking, and health monitoring.",
    lifespan=lifespan,
)

app.include_router(eth_router)
