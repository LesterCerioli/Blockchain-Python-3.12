import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from app.contract_generator import ERC20ContractGenerator
from app.services.aux.api.routers import router as aux_router
from app.services.defi.api.routers.defi_router import router as defi_router
from app.services.tokenization.api.routers.tokenization_router import router as tokenization_router
from app.services.tokenization.application.template_catalog_service import TemplateCatalogService
from app.services.tokenization.infrastructure.persistence.dynamodb_template_repository import DynamoDBTemplateRepository
from app.services.tokenization.infrastructure.audit.dynamodb_template_audit_logger import DynamoDBTemplateAuditLogger
from app.services.defi.application.quote_service import QuoteService
from app.services.defi.infrastructure.oracles.in_memory_price_oracle import (
    InMemoryPriceOracle,
)
from app.services.defi.infrastructure.repositories.in_memory_ohlcv_repository import (
    InMemoryOHLCVRepository,
)
from app.services.defi.infrastructure.repositories.in_memory_pool_repository import (
    InMemoryPoolRepository,
)
from app.services.defi.infrastructure.repositories.in_memory_token_repository import (
    InMemoryTokenRepository,
)
from app.services.defi.infrastructure.services.in_memory_swap_service import (
    InMemorySwapService,
)
from app.token_services import (
    prepare_contract_interaction_data,
)


def _get_database_url() -> str:
    """Read database URL from environment variables without exposing values."""
    dsn = os.getenv("DEFI_DATABASE_URL")
    if dsn:
        return dsn
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    name = os.getenv("DB_NAME", "blockchain_db")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = _get_database_url()
    token_repo = InMemoryTokenRepository(database_url=db_url)
    pool_repo = InMemoryPoolRepository(database_url=db_url)
    ohlcv_repo = InMemoryOHLCVRepository(database_url=db_url)
    price_oracle = InMemoryPriceOracle()
    swap_service = InMemorySwapService()
    app.state.defi_quote_service = QuoteService(
        token_repository=token_repo,
        pool_repository=pool_repo,
        price_oracle=price_oracle,
        swap_service=swap_service,
        ohlcv_repository=ohlcv_repo,
    )
    app.state.defi_ohlcv_repository = ohlcv_repo
    tokenization_repo = DynamoDBTemplateRepository()
    tokenization_audit = DynamoDBTemplateAuditLogger()
    app.state.tokenization_catalog_service = TemplateCatalogService(
        template_repository=tokenization_repo,
        audit_logger=tokenization_audit,
    )
    yield


app = FastAPI(title="FastChainBank", lifespan=lifespan)
app.include_router(defi_router)
app.include_router(aux_router)
app.include_router(tokenization_router)


class ERC20Properties(BaseModel):
    name: str
    symbol: str
    initial_supply: int
    decimals: int = 18


class ContractCodeResponse(BaseModel):
    solidity_code: str


class TokenServiceRequest(BaseModel):
    contract_address: str
    function_name: str
    args: list[Any]


class TokenServiceResponse(BaseModel):
    data: dict[str, Any]


@app.get("/")
async def root():
    return {"message": "Smart Contract Generator API"}


@app.post("/generate/erc20/", response_model=ContractCodeResponse)
async def generate_erc20_contract(properties: ERC20Properties):
    generator = ERC20ContractGenerator()
    code = generator.generate_contract(
        name=properties.name,
        symbol=properties.symbol,
        initial_supply=properties.initial_supply,
        decimals=properties.decimals,
    )
    return ContractCodeResponse(solidity_code=code)


@app.post("/service/prepare-contract-interaction/", response_model=TokenServiceResponse)
async def prepare_interaction_data(request: TokenServiceRequest):
    result = prepare_contract_interaction_data(
        contract_address=request.contract_address,
        function_name=request.function_name,
        args=request.args,
    )
    return TokenServiceResponse(data=result)
