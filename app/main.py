from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

from app.contract_generator import ERC20ContractGenerator
from app.services.defi.api.dependencies import get_research_report_service
from app.services.defi.api.routers import research_router
from app.services.defi.application.research_report_service import ResearchReportService
from app.services.defi.infrastructure.persistence import InMemoryResearchReportRepository
from app.token_services import format_token_transfer_data, prepare_contract_interaction_data


@asynccontextmanager
async def lifespan(application: FastAPI):
    report_repo = InMemoryResearchReportRepository()
    application.state.defi_research_service = ResearchReportService(repository=report_repo)
    yield


app = FastAPI(title="FastChainBank", lifespan=lifespan)
app.include_router(research_router)


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
    args: List[Any]

class TokenServiceResponse(BaseModel):
    data: Dict[str, Any]



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
        decimals=properties.decimals
    )
    return ContractCodeResponse(solidity_code=code)



@app.post("/service/prepare-contract-interaction/", response_model=TokenServiceResponse)
async def prepare_interaction_data(request: TokenServiceRequest):
    result = prepare_contract_interaction_data(
        contract_address=request.contract_address,
        function_name=request.function_name,
        args=request.args
    )
    return TokenServiceResponse(data=result)
