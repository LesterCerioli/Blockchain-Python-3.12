from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.routers.btc_router import router as btc_router
from .application.health_service import HealthService
from .application.network_service import NetworkService
from .domain.adapters.btc_node_adapter import BtcNodeAdapter
from .infrastructure.config.settings import BitcoinSettings
from .infrastructure.persistence.database import Database
from .infrastructure.persistence.node_repository import PostgresNodeRepository
from .infrastructure.providers.multi_provider import MultiProvider
from .infrastructure.providers.node_factory import NodeFactory


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = BitcoinSettings()

    node_config = {
        "name": "primary",
        "url": settings.rpc_url,
        "rpc_user": settings.rpc_user,
        "rpc_password": settings.rpc_password.get_secret_value(),
        "priority": 1,
        "request_timeout": settings.request_timeout,
        "circuit_breaker_failure_threshold": settings.circuit_breaker_failure_threshold,
        "circuit_breaker_recovery_seconds": settings.circuit_breaker_recovery_seconds,
    }

    db = Database(settings.database_url)
    providers = NodeFactory.create_from_config([node_config])
    multi_provider = MultiProvider(providers)
    node_adapter = BtcNodeAdapter(multi_provider)
    repository = PostgresNodeRepository(db)

    app.state.health_service = HealthService(
        node_adapter=node_adapter,
        providers=providers,
        repository=repository,
        stale_block_threshold_seconds=settings.stale_block_threshold_seconds,
    )
    app.state.network_service = NetworkService(node_adapter)
    app.state.multi_provider = multi_provider
    app.state.db = db

    yield

    await multi_provider.close()
    await db.close()


app = FastAPI(
    title="CryptoBank — Bitcoin RPC Service",
    version="1.0.0",
    description="Async Bitcoin Core RPC client with circuit breaking and health monitoring.",
    lifespan=lifespan,
)

app.include_router(btc_router)
