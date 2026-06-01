# GitHub Kanban — DeFi Module (Non-Custodial SaaS)

> Copy each block as an Issue in GitHub Projects.  
> **Suggested labels:** `epic`, `task`, `feature`, `phase-1`, `phase-2`, `compliance`, `blockchain`, `infra`, `api`  
> **Milestones:** `F1 – Zero-License MVP` · `F2 – Tokenization` · `F3 – Robo-Advisor (future)`

---

## EPIC 1 — DeFi Context Foundation
**Labels:** `epic` `phase-1`  
**Milestone:** F1 – Zero-License MVP

Establishes the isolated `services/defi/` *bounded context* inside the existing FastAPI/Python 3.12 monorepo. No DeFi logic must leak outside this context. Follows the same DDD layers already adopted in `services/blockchain/ethereum/` (domain → application → infrastructure → api).

**Epic acceptance criteria**
- [ ] Package `services/defi/` exists with the four DDD layers
- [ ] No import from `services/defi/` appears in code outside the context (verified by architecture test)
- [ ] DeFi router registered in `app/main.py` without breaking existing routes
- [ ] `DeFiSettings` separated from existing Ethereum settings

---

### TASK 1.1 — DDD Bounded Context Structure
**Labels:** `task` `phase-1` `epic-1`  
**Milestone:** F1  
**Parent:** EPIC 1

Create the directory structure and base domain types for the DeFi context, mirroring `services/blockchain/ethereum/`.

**Acceptance criteria**
- [ ] `services/defi/{domain,application,infrastructure,api}/__init__.py` exist
- [ ] Domain entities instantiable with Pydantic validation
- [ ] Value objects immutable with `__eq__` and `__hash__`
- [ ] Interfaces (ABCs) with no concrete implementation in the domain
- [ ] Exceptions inherit from `DeFiError` base

---

#### FEATURE 1.1.1 — Create `services/defi/` package with DDD layers
**Labels:** `feature` `phase-1` `task-1-1`  
**Parent Task:** TASK 1.1

**Technical description**  
Create the Python package structure mirroring `services/blockchain/ethereum/`:
```
services/defi/
  domain/
    entities/
    value_objects/
    interfaces/
    exceptions.py
  application/
  infrastructure/
    config/
    persistence/
    cache/
    market_data/
    workers/
    indexer/
    compliance/
    audit/
  api/
    routers/
    schemas/
    middleware/
```

**Implementation notes**
- Create only empty `__init__.py` files in this feature; content comes in subsequent features
- Add `services/defi/__init__.py` with `__all__ = []` to enforce explicit imports
- Do not reuse any imports from `services/blockchain/ethereum/` at this stage

**DoD**
- [ ] All directories created with `__init__.py`
- [ ] `pytest --collect-only` does not break with the new structure

---

#### FEATURE 1.1.2 — DeFi domain entities
**Labels:** `feature` `phase-1` `task-1-1`  
**Parent Task:** TASK 1.1  
**File:** `services/defi/domain/entities/`

**Technical description**  
Implement core entities using `@dataclass(frozen=True)` or Pydantic `BaseModel`:

- `Quote`: `symbol: str`, `price_usd: Decimal`, `change_24h: float`, `volume_24h: Decimal`, `market_cap: Decimal`, `fetched_at: datetime`
- `MarketIndex`: `index_id: str`, `name: str`, `components: list[IndexComponent]`, `value: Decimal`, `updated_at: datetime`
- `WalletSession`: `session_id: UUID`, `wallet_address: str`, `chain_id: int`, `created_at: datetime`, `expires_at: datetime` — **no private key field**
- `UnsignedTransaction`: `to: str`, `data: str`, `value: int`, `nonce: int`, `max_fee_per_gas: int`, `max_priority_fee_per_gas: int`, `chain_id: int`, `gas_limit: int` — **no `v`, `r`, `s` fields**
- `ResearchReport`: `report_id: UUID`, `title: str`, `body_markdown: str`, `published_at: datetime`, `categories: list[str]`, `tags: list[str]`, `version: int`

**Implementation notes**
- Use `Decimal` (not `float`) for monetary values
- `UnsignedTransaction` must not have `private_key`, `signature`, `signed_data` fields
- `WalletSession` stores only public address — add validator that rejects 64-hex-char strings (private key format)

**DoD**
- [ ] All entities instantiable with valid data
- [ ] `UnsignedTransaction` raises `ValueError` if any signing field is passed via `__init__`
- [ ] `WalletSession` raises `ValueError` if `wallet_address` has private key format (64 hex chars)
- [ ] Unit tests in `tests/defi/domain/test_entities.py`

---

#### FEATURE 1.1.3 — Immutable value objects
**Labels:** `feature` `phase-1` `task-1-1`  
**File:** `services/defi/domain/value_objects/`

**Technical description**  
- `TokenAddress`: `str` wrapper with EIP-55 checksum validation via `web3.is_checksum_address()`; `.checksummed() -> str` method
- `ChainId`: `int` validated against supported chain map (1=Ethereum, 137=Polygon, 42161=Arbitrum, 8453=Base)
- `FiatPrice`: `Decimal` >= 0 with `currency: str` (default `"USD"`)
- `CryptoAmount`: `Decimal` >= 0 with `token_address: TokenAddress` and `decimals: int`
- `TxHash`: `str` with format validation `0x` + 64 hex chars

**Implementation notes**
- Implement as `@dataclass(frozen=True)` — immutability is mandatory
- `TokenAddress.__eq__` and `__hash__` based on lowercase address
- `ChainId` with class method `ChainId.supported() -> list[int]`

**DoD**
- [ ] Value objects are not mutable (attempt `vo.field = x` raises `FrozenInstanceError`)
- [ ] `TokenAddress` rejects invalid addresses
- [ ] `ChainId` rejects unsupported chains
- [ ] Unit tests covering invalid cases

---

#### FEATURE 1.1.4 — Domain interfaces (Ports)
**Labels:** `feature` `phase-1` `task-1-1`  
**File:** `services/defi/domain/interfaces/`

**Technical description**  
ABCs defining contracts between domain and infrastructure:

```python
# IMarketDataProvider
async def get_quote(symbol: str) -> Quote: ...
async def get_quotes(symbols: list[str]) -> list[Quote]: ...
async def get_ohlcv(symbol: str, interval: str, from_ts: datetime, to_ts: datetime) -> list[OHLCVCandle]: ...

# IWalletConnector
async def validate_address(address: str) -> bool: ...
async def resolve_ens(name: str) -> str | None: ...

# ITransactionBuilder
async def build_erc20_transfer(from_addr: str, to_addr: str, token: TokenAddress, amount: CryptoAmount, chain_id: ChainId) -> UnsignedTransaction: ...
async def estimate_gas(tx: UnsignedTransaction) -> int: ...

# IResearchRepository
async def save(report: ResearchReport) -> None: ...
async def find_by_id(report_id: UUID) -> ResearchReport | None: ...
async def search(query: str, page: int, page_size: int) -> list[ResearchReport]: ...
```

**DoD**
- [ ] All ABCs with `@abstractmethod` on every method
- [ ] No concrete implementation in the interface file
- [ ] Importable without external dependencies (only stdlib + domain)

---

#### FEATURE 1.1.5 — DeFi exception hierarchy
**Labels:** `feature` `phase-1` `task-1-1`  
**File:** `services/defi/domain/exceptions.py`

**Technical description**
```python
class DeFiError(Exception): ...
class MarketDataError(DeFiError): ...
class ProviderUnavailableError(MarketDataError): ...
class RateLimitError(MarketDataError): ...
class WalletConnectionError(DeFiError): ...
class InvalidAddressError(WalletConnectionError): ...
class NonCustodialViolationError(DeFiError): ...  # raised when code attempts to touch a private key
class SanctionedAddressError(DeFiError): ...
class ToUNotAcceptedError(DeFiError): ...
class IndexerLagError(DeFiError): ...
```

**DoD**
- [ ] Hierarchy reflects the structure above
- [ ] `NonCustodialViolationError` has `violation_type: str` field describing what was violated
- [ ] All exceptions serializable to JSON (`to_dict()` method)

---

### TASK 1.2 — API Contract and Routing
**Labels:** `task` `phase-1` `epic-1`  
**Parent:** EPIC 1

**Acceptance criteria**
- [ ] `GET /api/v1/defi/health` returns `{"status": "ok"}`
- [ ] Existing routes (`/api/v1/blockchain/...`) continue working
- [ ] OpenAPI spec at `/docs` displays separate DeFi tags with non-custodial model description

---

#### FEATURE 1.2.1 — DeFi router registered in FastAPI
**Labels:** `feature` `phase-1` `task-1-2`  
**Files:** `services/defi/api/routers/__init__.py`, `app/main.py`

**Technical description**  
Create `defi_router = APIRouter(prefix="/api/v1/defi", tags=["DeFi"])` and register it in `app/main.py` via `app.include_router(defi_router)`. Add sub-routers per module: `quotes_router`, `wallet_router`, `research_router`, `portfolio_router`.

**DoD**
- [ ] `GET /api/v1/defi/health` returns 200
- [ ] No existing route broken (run `pytest tests/test_api.py`)
- [ ] DeFi tags appear in `/docs`

---

#### FEATURE 1.2.2 — Shared response schemas
**Labels:** `feature` `phase-1` `task-1-2`  
**File:** `services/defi/api/schemas/common.py`

**Technical description**
```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    request_id: str

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    components: dict[str, str]
```

**DoD**
- [ ] `PaginatedResponse` generic works with any type `T`
- [ ] `ErrorResponse` returned in all DeFi exception handlers
- [ ] Serialization tests in `tests/defi/api/test_schemas.py`

---

#### FEATURE 1.2.3 — DeFi FastAPI dependencies
**Labels:** `feature` `phase-1` `task-1-2`  
**File:** `services/defi/api/dependencies.py`

**Technical description**
```python
async def get_defi_settings() -> DeFiSettings: ...
async def get_market_provider(settings: DeFiSettings = Depends(...)) -> IMarketDataProvider: ...
async def get_wallet_service(settings: DeFiSettings = Depends(...)) -> WalletSessionService: ...
async def get_current_wallet_session(token: str = Header(...)) -> WalletSession: ...
```
`get_current_wallet_session` validates the session token and returns the session; raises HTTP 401 if invalid.

**DoD**
- [ ] Dependencies use `lru_cache` or `Depends` singleton to avoid multiple instances
- [ ] `get_current_wallet_session` never exposes a private key under any circumstance
- [ ] Tests with `TestClient` and mocked dependencies

---

#### FEATURE 1.2.4 — Non-custodial OpenAPI tags
**Labels:** `feature` `phase-1` `task-1-2`  
**File:** `app/main.py`

**Technical description**  
Add `openapi_tags` in `FastAPI(...)` with explicit descriptions:
```python
{"name": "DeFi – Quotes", "description": "Read-only market data. Zero license."},
{"name": "DeFi – Wallet", "description": "Non-custodial connection. Keys never leave the client."},
{"name": "DeFi – Research", "description": "Impersonal content published equally to all subscribers."},
```

**DoD**
- [ ] Tags visible in `/docs` with the descriptions above
- [ ] Each DeFi router uses the corresponding tag

---

### TASK 1.3 — Configuration and Environment
**Labels:** `task` `phase-1` `epic-1`  
**Parent:** EPIC 1

**Acceptance criteria**
- [ ] `DeFiSettings` loads from environment variables without conflicting with existing `EthereumSettings`
- [ ] `.env.example` updated with all DeFi variables documented
- [ ] No DeFi configuration variable accepts a value that looks like a private key

---

#### FEATURE 1.3.1 — `DeFiSettings` with Pydantic Settings
**Labels:** `feature` `phase-1` `task-1-3`  
**File:** `services/defi/infrastructure/config/settings.py`

**Technical description**
```python
class DeFiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DEFI_", env_file=".env")

    coingecko_api_key: SecretStr | None = None
    cmc_api_key: SecretStr | None = None
    redis_url: str = "redis://localhost:6379/1"
    quote_cache_ttl_seconds: int = 30
    history_cache_ttl_seconds: int = 300
    market_data_timeout_seconds: int = 10
    max_symbols_per_batch: int = 50
    ofac_api_key: SecretStr | None = None
```
Use `SecretStr` for all API keys — never plain `str` for secrets.

**DoD**
- [ ] `DeFiSettings()` instantiable without defined variables (all fields have defaults)
- [ ] API keys are `SecretStr` and do not appear in `repr()` or logs
- [ ] Test verifying `repr(settings)` does not contain the key value

---

#### FEATURE 1.3.2 — Multi-chain configuration
**Labels:** `feature` `phase-1` `task-1-3`  
**File:** `services/defi/infrastructure/config/settings.py`

**Technical description**  
Add to `DeFiSettings`:
```python
chains: dict[int, ChainConfig] = {
    1:     ChainConfig(name="Ethereum Mainnet",  rpc_url="...", explorer="https://etherscan.io"),
    137:   ChainConfig(name="Polygon",           rpc_url="...", explorer="https://polygonscan.com"),
    42161: ChainConfig(name="Arbitrum One",      rpc_url="...", explorer="https://arbiscan.io"),
    8453:  ChainConfig(name="Base",              rpc_url="...", explorer="https://basescan.org"),
}
```
Where `ChainConfig` has `name`, `rpc_url: SecretStr`, `explorer: str`, `is_testnet: bool = False`.

**DoD**
- [ ] RPC URLs are `SecretStr`
- [ ] `ChainId` value object validates against `settings.chains.keys()`
- [ ] Testnet chains (Sepolia=11155111, Mumbai=80001) supported with `is_testnet=True`

---

#### FEATURE 1.3.3 — Updated `.env.example`
**Labels:** `feature` `phase-1` `task-1-3`

**Technical description**  
Add DeFi section to `.env.example`:
```
# DeFi Module
DEFI_COINGECKO_API_KEY=your_key_here
DEFI_CMC_API_KEY=your_key_here
DEFI_REDIS_URL=redis://localhost:6379/1
DEFI_QUOTE_CACHE_TTL_SECONDS=30
DEFI_OFAC_API_KEY=your_key_here
DEFI_CHAINS__1__RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
DEFI_CHAINS__137__RPC_URL=https://polygon-rpc.com
```

**DoD**
- [ ] No real keys in `.env.example` (placeholders only)
- [ ] Comments explaining each variable
- [ ] `.env` remains in `.gitignore`

---

#### FEATURE 1.3.4 — Configuration tests
**Labels:** `feature` `phase-1` `task-1-3`  
**File:** `tests/defi/test_settings.py`

**Technical description**  
Tests ensuring `DeFiSettings` does not leak secrets and validations work.

**DoD**
- [ ] `repr(DeFiSettings(coingecko_api_key="secret123"))` does not contain `"secret123"`
- [ ] `DeFiSettings` with unsupported `chain_id` raises `ValidationError`
- [ ] Test that chain RPC URL does not appear in `uvicorn.access` logs

---

## EPIC 2 — Quotes & Indices
**Labels:** `epic` `phase-1` `blockchain`  
**Milestone:** F1 – Zero-License MVP

Read-only information product. All data is impersonal — identical for all subscribers. Acquisition flagship. Lowest regulatory risk on the platform.

**Epic acceptance criteria**
- [ ] `GET /api/v1/defi/quotes/BTC` returns price in under 200ms (warm cache)
- [ ] Automatic failover between CoinGecko and CMC with no client-facing error
- [ ] No quote response contains `user_id` or `wallet_address`
- [ ] Redis cache operating with configurable TTL

---

### TASK 2.1 — Market Data Provider Integration
**Labels:** `task` `phase-1` `epic-2` `blockchain`  
**Parent:** EPIC 2

**Acceptance criteria**
- [ ] CoinGecko adapter functional for spot prices and history
- [ ] CMC adapter functional as fallback
- [ ] Circuit breaker activates after 3 consecutive failures on any provider
- [ ] Rate limiting respects Free plan limits (CoinGecko: 10–30 req/min)

---

#### FEATURE 2.1.1 — CoinGecko adapter
**Labels:** `feature` `phase-1` `task-2-1`  
**File:** `services/defi/infrastructure/market_data/coingecko_adapter.py`

**Technical description**  
Implements `IMarketDataProvider` using `httpx.AsyncClient`:
- `get_quote(symbol)` → `GET /api/v3/simple/price?ids={coingecko_id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true`
- `get_quotes(symbols)` → same endpoint with multiple ids
- `get_ohlcv(symbol, interval, from_ts, to_ts)` → `GET /api/v3/coins/{id}/ohlc`
- Symbol (`BTC`) to coingecko_id (`bitcoin`) mapping via static dictionary; later via `GET /api/v3/coins/list`

**Implementation notes**
- Inject `httpx.AsyncClient` via constructor (not created inside the method) for connection reuse
- `API_KEY` passed as `x-cg-pro-api-key` header if available; otherwise uses public endpoint
- Treat HTTP 429 by raising `RateLimitError`
- Treat HTTP 5xx by raising `ProviderUnavailableError`

**DoD**
- [ ] Unit tests with `httpx_mock` or `respx` mocking responses
- [ ] `RateLimitError` raised on HTTP 429
- [ ] BTC→bitcoin, ETH→ethereum, SOL→solana mappings working

---

#### FEATURE 2.1.2 — CoinMarketCap adapter
**Labels:** `feature` `phase-1` `task-2-1`  
**File:** `services/defi/infrastructure/market_data/cmc_adapter.py`

**Technical description**  
Implements `IMarketDataProvider`:
- `GET /v1/cryptocurrency/quotes/latest?symbol={SYMBOL}&convert=USD`
- Header: `X-CMC_PRO_API_KEY: {key}`
- Same error handling as CoinGecko (429 → `RateLimitError`, 5xx → `ProviderUnavailableError`)

**DoD**
- [ ] Same interface as CoinGecko (substitutable without changing the application layer)
- [ ] Unit tests with mocked responses

---

#### FEATURE 2.1.3 — `MultiMarketDataProvider` with failover
**Labels:** `feature` `phase-1` `task-2-1`  
**File:** `services/defi/infrastructure/market_data/multi_provider.py`

**Technical description**  
Reuse the pattern from `services/blockchain/ethereum/infrastructure/providers/multi_provider.py`:
- Ordered list of providers; tries primary first
- On `ProviderUnavailableError` or `RateLimitError`, tries next
- Integrate the existing `circuit_breaker.py` from `services/blockchain/ethereum/infrastructure/rpc/`
- Expose `MultiMarketDataProvider` as concrete implementation of `IMarketDataProvider`

**DoD**
- [ ] With primary simulating failure, data comes from secondary transparently
- [ ] Circuit breaker opens after 3 failures; closes after 30s
- [ ] Failover tests in `tests/defi/market_data/test_multi_provider.py`

---

#### FEATURE 2.1.4 — Rate limiting with exponential backoff
**Labels:** `feature` `phase-1` `task-2-1`

**Technical description**  
Inside each adapter, implement retry with `tenacity`:
```python
@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
)
async def _request(self, ...): ...
```
Proactive rate control: request counter per 60s window in Redis; reject before calling the API if at the limit.

**DoD**
- [ ] Maximum 3 retries with exponential backoff
- [ ] Redis counter at `defi:rate_limit:{provider_name}:{window}`
- [ ] Test simulating 429 verifies backoff occurs

---

#### FEATURE 2.1.5 — Market data integration tests
**Labels:** `feature` `phase-1` `task-2-1`  
**File:** `tests/defi/market_data/`

**Technical description**  
- Unit tests: mocks via `respx` for CoinGecko and CMC
- Integration tests (marked `@pytest.mark.integration`): call real APIs with sandbox key; run only in CI with `RUN_INTEGRATION_TESTS=true`

**DoD**
- [ ] `pytest -m "not integration"` passes without network
- [ ] Coverage > 80% on adapters

---

### TASK 2.2 — Quotes Service
**Labels:** `task` `phase-1` `epic-2`  
**Parent:** EPIC 2

**Acceptance criteria**
- [ ] `GET /api/v1/defi/quotes/BTC` returns JSON with `symbol`, `price_usd`, `change_24h`, `volume_24h`, `market_cap`, `fetched_at`
- [ ] Cache hit returns in < 10ms; cache miss in < 500ms
- [ ] Batch of 50 symbols works in a single call

---

#### FEATURE 2.2.1 — `QuoteService`
**Labels:** `feature` `phase-1` `task-2-2`  
**File:** `services/defi/application/quote_service.py`

**Technical description**
```python
class QuoteService:
    def __init__(self, provider: IMarketDataProvider, cache: IQuoteCache): ...
    async def get_quote(self, symbol: str) -> Quote: ...
    async def get_quotes(self, symbols: list[str]) -> list[Quote]: ...
    async def get_ohlcv(self, symbol: str, interval: str, from_ts: datetime, to_ts: datetime) -> list[OHLCVCandle]: ...
```
Cache-aside: tries cache first; on miss, calls provider and populates cache.

**DoD**
- [ ] Cache hit does not call the provider (verified by mock)
- [ ] `get_quotes` with empty list returns `[]` without calling provider
- [ ] Unit tests with mocked provider and cache

---

#### FEATURE 2.2.2 — `GET /defi/quotes/{symbol}`
**Labels:** `feature` `phase-1` `task-2-2`  
**File:** `services/defi/api/routers/quotes_router.py`

**Technical description**
```
GET /api/v1/defi/quotes/{symbol}
Response 200: QuoteResponse
  symbol: str
  price_usd: str  # Decimal serialized as string to avoid precision loss
  change_24h_pct: float
  volume_24h_usd: str
  market_cap_usd: str
  fetched_at: datetime (ISO 8601)
Response 404: ErrorResponse (symbol not found)
Response 503: ErrorResponse (all providers unavailable)
```

**DoD**
- [ ] Returns 200 with correct fields for `BTC`, `ETH`
- [ ] Returns 404 for non-existent symbol
- [ ] `price_usd` is a string (not float) in JSON

---

#### FEATURE 2.2.3 — `GET /defi/quotes` (batch)
**Labels:** `feature` `phase-1` `task-2-2`

**Technical description**
```
GET /api/v1/defi/quotes?symbols=BTC,ETH,SOL
Response 200: list[QuoteResponse]
```
Validate `len(symbols) <= 50`; return HTTP 422 with clear message if exceeded.

**DoD**
- [ ] 50 symbols work
- [ ] 51 symbols return 422
- [ ] Symbols with spaces are trimmed

---

#### FEATURE 2.2.4 — `GET /defi/quotes/{symbol}/history`
**Labels:** `feature` `phase-1` `task-2-2`

**Technical description**
```
GET /api/v1/defi/quotes/{symbol}/history?interval=1h&from=2026-01-01T00:00:00Z&to=2026-01-02T00:00:00Z
Response 200: OHLCVResponse
  symbol: str
  interval: str
  candles: list[OHLCVCandle]
    open_time: datetime
    open: str
    high: str
    low: str
    close: str
    volume: str
```
Valid intervals: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`, `1w`.

**DoD**
- [ ] Invalid interval returns 422
- [ ] Range > 365 days returns 422 with message
- [ ] OHLCV values are strings (serialized Decimal)

---

#### FEATURE 2.2.5 — Redis cache for quotes
**Labels:** `feature` `phase-1` `task-2-2`  
**File:** `services/defi/infrastructure/cache/redis_quote_cache.py`

**Technical description**  
Implements `IQuoteCache` interface:
- Key: `defi:quote:{symbol}` (spot), `defi:ohlcv:{symbol}:{interval}:{from}:{to}` (history)
- Serialization: JSON with `orjson` for performance
- TTL: `DEFI_QUOTE_CACHE_TTL_SECONDS` (spot), `DEFI_HISTORY_CACHE_TTL_SECONDS` (history)
- Use `redis.asyncio`

**DoD**
- [ ] Cache miss populates Redis correctly
- [ ] `redis-cli TTL defi:quote:BTC` returns value close to 30
- [ ] Integration test with real Redis (marked `@pytest.mark.integration`)

---

### TASK 2.3 — Market Indices and Rankings
**Labels:** `task` `phase-1` `epic-2`  
**Parent:** EPIC 2

**Acceptance criteria**
- [ ] `GET /api/v1/defi/rankings/tokens?metric=market_cap` returns top 100 paginated
- [ ] Rankings updated every 15 minutes via worker
- [ ] No ranking contains user-personalized data

---

#### FEATURE 2.3.1 — `IndexService`
**Labels:** `feature` `phase-1` `task-2-3`  
**File:** `services/defi/application/index_service.py`

**Technical description**
```python
class IndexService:
    async def list_indices(self) -> list[MarketIndex]: ...
    async def get_index(self, index_id: str) -> MarketIndex: ...
    async def get_token_rankings(self, metric: str, chain: str | None, page: int, page_size: int) -> PaginatedResponse[TokenRanking]: ...
    async def get_protocol_rankings(self, metric: str) -> list[ProtocolRanking]: ...
```

**DoD**
- [ ] `list_indices` returns at least `defi-tvl-top20` and `top100-market-cap`
- [ ] Unit tests with mocked data

---

#### FEATURE 2.3.2 — Index endpoints
**Labels:** `feature` `phase-1` `task-2-3`

**Technical description**
```
GET /api/v1/defi/indices → list[IndexSummaryResponse]
GET /api/v1/defi/indices/{index_id} → IndexDetailResponse
  index_id, name, description, value, change_24h_pct, components: list[IndexComponent], updated_at
```

**DoD**
- [ ] 200 with list of available indices
- [ ] 404 for non-existent index_id

---

#### FEATURE 2.3.3 — `GET /defi/rankings/tokens`
**Labels:** `feature` `phase-1` `task-2-3`

**Technical description**
```
GET /api/v1/defi/rankings/tokens?metric=market_cap&chain=ethereum&page=1&page_size=20
Valid metrics: market_cap, volume_24h, price_change_24h
Response: PaginatedResponse[TokenRanking]
  rank: int, symbol: str, name: str, metric_value: str, price_usd: str
```

**DoD**
- [ ] Pagination functional (page/page_size with limits)
- [ ] Invalid metric returns 422
- [ ] No `user_id` field in response (impersonality guard)

---

#### FEATURE 2.3.4 — `GET /defi/rankings/protocols` via DeFiLlama
**Labels:** `feature` `phase-1` `task-2-3`  
**File:** `services/defi/infrastructure/market_data/defillama_adapter.py`

**Technical description**  
Adapter for `https://api.llama.fi/protocols`:
- `GET /protocols` → TVL per protocol
- `GET /v2/historicalChainTvl/{chain}` → historical TVL per chain
- No authentication (public API)

**DoD**
- [ ] TVL rankings returned and cached (TTL 15 min)
- [ ] Tests with `respx` mocking DeFiLlama

---

#### FEATURE 2.3.5 — Rankings refresh worker
**Labels:** `feature` `phase-1` `task-2-3`  
**File:** `services/defi/infrastructure/workers/tasks.py`

**Technical description**  
Task `refresh_rankings` scheduled every 15 minutes:
- Calls `IndexService.get_protocol_rankings()` and persists in Redis with 20 min TTL
- On failure, keeps previous cache (never returns empty data)

**DoD**
- [ ] Worker executes without error in development environment
- [ ] On provider failure, previous data is maintained

---

## EPIC 3 — Non-Custodial Wallet & Transactions
**Labels:** `epic` `phase-1` `blockchain` `compliance`  
**Milestone:** F1 – Zero-License MVP

Architectural invariant: **the platform builds the unsigned transaction; the client signs on their own device; funds never pass through the company.** Any violation of this invariant is `NonCustodialViolationError` and must break the build via architecture test.

**Epic acceptance criteria**
- [ ] `POST /defi/wallet/connect` with valid public address returns session token
- [ ] `POST /defi/transactions/estimate` returns `UnsignedTransaction` without signature fields
- [ ] `POST /defi/transactions/broadcast` accepts only externally-signed tx
- [ ] Architecture test passes: no DeFi module signs transactions on the server

---

### TASK 3.1 — Wallet Connection
**Labels:** `task` `phase-1` `epic-3`  
**Parent:** EPIC 3

**Acceptance criteria**
- [ ] Session stores only public address + chain_id
- [ ] ENS resolves to EVM address
- [ ] Disconnect revokes session without error (no key data to delete)

---

#### FEATURE 3.1.1 — `WalletSessionService`
**Labels:** `feature` `phase-1` `task-3-1`  
**File:** `services/defi/application/wallet_session_service.py`

**Technical description**
```python
class WalletSessionService:
    async def connect(self, wallet_address: str, chain_id: int) -> WalletSession: ...
    async def disconnect(self, session_id: UUID) -> None: ...
    async def get_session(self, session_id: UUID) -> WalletSession | None: ...
```
- Generates `session_id` as UUID4
- Stores in Redis: `defi:session:{session_id}` with 24h TTL (only public address + chain_id)
- **Never** stores or accepts a private key

**DoD**
- [ ] `connect` with invalid address raises `InvalidAddressError`
- [ ] Expired session returns `None` in `get_session`
- [ ] Redis inspection after `connect` shows only public address

---

#### FEATURE 3.1.2 — `POST /defi/wallet/connect`
**Labels:** `feature` `phase-1` `task-3-1`

**Technical description**
```
POST /api/v1/defi/wallet/connect
Body: { "wallet_address": "0x...", "chain_id": 1 }
Response 200: { "session_token": "uuid", "wallet_address": "0x...", "chain_id": 1, "expires_at": "..." }
Response 422: invalid address or unsupported chain
```
Sanctions middleware (`SanctionsGuard`) executes before creating session.

**DoD**
- [ ] Returns 200 with session_token for valid address
- [ ] Sanctioned address returns 403 with `error_code: "sanctioned_address"`
- [ ] Unsupported chain returns 422

---

#### FEATURE 3.1.3 — EIP-55 validation and ENS resolution
**Labels:** `feature` `phase-1` `task-3-1`  
**File:** `services/defi/domain/value_objects/token_address.py`

**Technical description**  
In `TokenAddress.__post_init__`:
- If starts with `0x` and has 42 chars: validate EIP-55 checksum via `web3.Web3.is_checksum_address()`
- If ends with `.eth`: resolve ENS via `web3_instance.ens.address(name)` and store resolved address
- Normalize to checksum before storing

**DoD**
- [ ] `TokenAddress("0xinvalid")` raises `InvalidAddressError`
- [ ] `TokenAddress("vitalik.eth")` resolves to correct address (integration test)
- [ ] Lowercase address is normalized to checksum

---

#### FEATURE 3.1.4 — `DELETE /defi/wallet/disconnect`
**Labels:** `feature` `phase-1` `task-3-1`

**Technical description**
```
DELETE /api/v1/defi/wallet/disconnect
Header: Authorization: Bearer {session_token}
Response 204: session revoked
Response 401: invalid session_token
```
Deletes key `defi:session:{session_id}` from Redis. No sensitive data to delete (non-custodial design).

**DoD**
- [ ] Redis no longer contains the key after disconnect
- [ ] Second disconnect with same token returns 204 (idempotent)

---

#### FEATURE 3.1.5 — Session non-custodial boundary test
**Labels:** `feature` `phase-1` `task-3-1` `compliance`  
**File:** `tests/defi/test_non_custodial_boundary.py`

**Technical description**  
Architecture tests using `ast.parse`:
- Scan all files in `services/defi/` looking for fields named `private_key`, `seed_phrase`, `mnemonic`, `keystore`, `secret_key`
- Fail the test if any assignment to these names is found in entities or schemas

**DoD**
- [ ] Test passes with current code
- [ ] Adding `private_key` to any entity causes the test to fail

---

### TASK 3.2 — Unsigned Transaction Builder
**Labels:** `task` `phase-1` `epic-3` `blockchain`  
**Parent:** EPIC 3

**Acceptance criteria**
- [ ] `POST /defi/transactions/estimate` returns object without `v`, `r`, `s`, `signature` fields
- [ ] ERC-20 transfer builder functional on Ethereum and Polygon
- [ ] Middleware rejects payloads with `private_key` with HTTP 422

---

#### FEATURE 3.2.1 — `TransactionBuilderService`
**Labels:** `feature` `phase-1` `task-3-2`  
**File:** `services/defi/application/transaction_builder_service.py`

**Technical description**
```python
class TransactionBuilderService:
    async def build(self, builder: ITransactionBuilder, params: dict) -> UnsignedTransaction: ...
    async def estimate_gas(self, tx: UnsignedTransaction) -> int:
        # web3.eth.estimate_gas(tx.to_dict()) — read-only call
    async def get_fee_data(self, chain_id: int) -> FeeData:
        # web3.eth.get_block("pending") for maxFeePerGas and maxPriorityFeePerGas
```
`build()` verifies the result is `UnsignedTransaction` without signature fields before returning.

**DoD**
- [ ] `build()` raises `NonCustodialViolationError` if `UnsignedTransaction` has `signature` field
- [ ] `estimate_gas` uses `eth_estimateGas` (read-only, does not send tx)
- [ ] Unit tests with mocked web3

---

#### FEATURE 3.2.2 — `POST /defi/transactions/estimate`
**Labels:** `feature` `phase-1` `task-3-2`

**Technical description**
```
POST /api/v1/defi/transactions/estimate
Header: Authorization: Bearer {session_token}
Body: {
  "type": "erc20_transfer",  // or "erc20_approve", "uniswap_swap"
  "params": { "token_address": "0x...", "to": "0x...", "amount": "1000000" }
}
Response 200: {
  "unsigned_tx": {
    "to": "0x...", "data": "0x...", "value": "0",
    "nonce": 42, "chain_id": 1,
    "max_fee_per_gas": "...", "max_priority_fee_per_gas": "...", "gas_limit": 65000
  },
  "estimated_gas": 65000,
  "estimated_fee_usd": "2.50"
}
```

**DoD**
- [ ] Response **does not contain** `signature`, `v`, `r`, `s`
- [ ] Correct `nonce` for session address via `eth_getTransactionCount`
- [ ] `estimated_fee_usd` calculated from gas price and ETH quote

---

#### FEATURE 3.2.3 — ERC-20 builder
**Labels:** `feature` `phase-1` `task-3-2`  
**File:** `services/defi/domain/builders/erc20_tx_builder.py`

**Technical description**  
Using standard ERC-20 ABI and `web3.py`:
- `transfer(address to, uint256 amount)` → `contract.encodeABI(fn_name='transfer', args=[to, amount])`
- `approve(address spender, uint256 amount)`
- `transferFrom(address from, address to, uint256 amount)`

**DoD**
- [ ] Generated hex `data` correctly verified against ERC-20 ABI
- [ ] `value` always `0` for token transfers (zero ETH value)
- [ ] Tests with real ERC-20 token on testnet (marked `@pytest.mark.integration`)

---

#### FEATURE 3.2.4 — Uniswap V2/V3 builder
**Labels:** `feature` `phase-1` `task-3-2`  
**File:** `services/defi/domain/builders/uniswap_tx_builder.py`

**Technical description**  
- V2: `swapExactTokensForTokens`, `swapExactETHForTokens` via Router V2 ABI
- V3: `exactInputSingle` via SwapRouter V3 ABI
- Calculate `amountOutMin` with configurable slippage (default 0.5%)
- `deadline` = `int(time.time()) + 300` (5 min)

**DoD**
- [ ] Calldata decodable via ABI
- [ ] No tx submission — only `data` assembly

---

#### FEATURE 3.2.5 — `NonCustodialGuard` middleware
**Labels:** `feature` `phase-1` `task-3-2` `compliance`  
**File:** `services/defi/api/middleware/non_custodial_guard.py`

**Technical description**  
`BaseHTTPMiddleware` that inspects each request body:
```python
FORBIDDEN_FIELDS = {"private_key", "seed_phrase", "mnemonic", "keystore", "secret_key", "privateKey", "seedPhrase"}
```
If any JSON body key matches `FORBIDDEN_FIELDS` (case-insensitive), returns HTTP 422:
```json
{"error_code": "non_custodial_violation", "message": "Private key fields are not accepted by this platform."}
```

**DoD**
- [ ] POST with `{"private_key": "0x..."}` returns 422
- [ ] POST with `{"wallet_address": "0x..."}` passes normally
- [ ] Middleware does not log the value of the forbidden field (only the key name)
- [ ] Test `tests/defi/api/test_non_custodial_guard.py`

---

#### FEATURE 3.2.6 — Builder non-custody tests
**Labels:** `feature` `phase-1` `task-3-2` `compliance`  
**File:** `tests/defi/test_tx_builder.py`

**DoD**
- [ ] `TransactionBuilderService.build()` with mock returning `UnsignedTransaction` with extra `signature` field raises `NonCustodialViolationError`
- [ ] Call to `eth_account.Account.sign_transaction` inside `services/defi/` detected by AST test and fails

---

### TASK 3.3 — Transaction Broadcast and Monitoring
**Labels:** `task` `phase-1` `epic-3` `blockchain`  
**Parent:** EPIC 3

**Acceptance criteria**
- [ ] `POST /defi/transactions/broadcast` with valid signed tx returns `tx_hash`
- [ ] `GET /defi/transactions/{hash}/status` returns correct status
- [ ] Second broadcast with same `Idempotency-Key` returns same `tx_hash` without resubmission

---

#### FEATURE 3.3.1 — `POST /defi/transactions/broadcast`
**Labels:** `feature` `phase-1` `task-3-3`

**Technical description**
```
POST /api/v1/defi/transactions/broadcast
Header: Authorization: Bearer {session_token}
Header: Idempotency-Key: {uuid}
Body: { "signed_tx_hex": "0x02f87..." }
Response 202: { "tx_hash": "0x...", "status": "pending" }
Response 200: { "tx_hash": "0x..." }  // idempotent repeat (same key)
```
Calls `web3.eth.send_raw_transaction(HexBytes(signed_tx_hex))`. Server only propagates — never creates the signed tx.

**DoD**
- [ ] `tx_hash` returned is the real network hash
- [ ] Malformed TX returns 422 before attempting submission
- [ ] Record in table `defi_broadcasts` with `idempotency_key`, `tx_hash`, `wallet_address`, `broadcast_at`

---

#### FEATURE 3.3.2 — `GET /defi/transactions/{tx_hash}/status`
**Labels:** `feature` `phase-1` `task-3-3`

**Technical description**
```
GET /api/v1/defi/transactions/{tx_hash}/status
Response 200: {
  "tx_hash": "0x...", "status": "confirmed",
  "block_number": 19000000, "confirmations": 12, "gas_used": 65000,
  "timestamp": "2026-05-31T12:00:00Z"
}
Status: pending | confirmed | failed | not_found
```
Uses `web3.eth.get_transaction_receipt(tx_hash)`; if `None`, status = `pending`.

**DoD**
- [ ] Invalid hash (non-hex) returns 422
- [ ] Valid hash not found returns 200 with `status: "not_found"`
- [ ] `confirmations` calculated as `current_block - receipt.blockNumber`

---

#### FEATURE 3.3.3 — Transaction confirmation worker
**Labels:** `feature` `phase-1` `task-3-3` `infra`  
**File:** `services/defi/infrastructure/workers/tx_confirmation_worker.py`

**Technical description**  
Task `confirm_transaction(tx_hash: str, webhook_url: str | None)`:
1. Polling every 15s for up to 5 min on `eth_getTransactionReceipt`
2. On confirmation, updates status in `defi_broadcasts`
3. If `webhook_url` provided, `POST webhook_url` with `TxStatusResponse`

**DoD**
- [ ] Worker does not hang if tx never confirms (5 min timeout)
- [ ] Webhook has retry with backoff (3 attempts)
- [ ] Unit tests with mocked web3 and httpx

---

#### FEATURE 3.3.4 — Broadcast idempotency
**Labels:** `feature` `phase-1` `task-3-3`  
**File:** `services/defi/api/middleware/idempotency_middleware.py`

**Technical description**  
Middleware for `POST /defi/transactions/broadcast` routes:
- Reads header `Idempotency-Key` (required UUID)
- Checks in Redis `defi:idempotency:{key}`
- If exists: returns cached response with HTTP 200
- If not: processes, stores response with 24h TTL

**DoD**
- [ ] Second request with same `Idempotency-Key` returns the same response
- [ ] Request without `Idempotency-Key` returns 422

---

#### FEATURE 3.3.5 — `GET /defi/transactions/history`
**Labels:** `feature` `phase-1` `task-3-3`

**Technical description**
```
GET /api/v1/defi/transactions/history?wallet=0x...&page=1&page_size=20
Response: PaginatedResponse[TxHistoryItem]
  tx_hash, status, type, from_address, to_address, value, gas_used, block_number, timestamp
```
Queries table `defi_indexed_events` from the indexer (Epic 5). Filtered by `wallet_address`.

**DoD**
- [ ] Depends on EPIC 5 (indexer) — mark as blocked
- [ ] Returns 200 with empty list if no history (not 404)

---

### TASK 3.4 — Portfolio View (Read-Only)
**Labels:** `task` `phase-1` `epic-3` `blockchain`  
**Parent:** EPIC 3

**Acceptance criteria**
- [ ] `GET /defi/portfolio/{address}/balances` returns ETH + ERC-20 balances in < 2s
- [ ] No write operation when querying portfolio
- [ ] Sanctioned address returns 403

---

#### FEATURE 3.4.1 — `GET /defi/portfolio/{address}/balances`
**Labels:** `feature` `phase-1` `task-3-4`

**Technical description**
```
GET /api/v1/defi/portfolio/{wallet_address}/balances?chain_id=1
Response 200: {
  "wallet_address": "0x...",
  "chain_id": 1,
  "native_balance": "1.5",  // in ETH, not Wei
  "tokens": [
    { "token_address": "0x...", "symbol": "USDC", "balance": "1000.00", "decimals": 6 }
  ]
}
```
`native_balance` via `web3.eth.get_balance()`; tokens via Multicall3 (see 3.4.2).

**DoD**
- [ ] Balance in human-readable units (not Wei)
- [ ] Token list based on curated token list (not all tokens on chain)

---

#### FEATURE 3.4.2 — Multicall3 ERC-20 batch reader
**Labels:** `feature` `phase-1` `task-3-4`  
**File:** `services/defi/infrastructure/chain/multicall_reader.py`

**Technical description**  
Uses `Multicall3` contract (address `0xcA11bde05977b3631167028862bE2a173976CA11` — same on all EVM chains) to make multiple `eth_call` in a single RPC call:
```python
async def get_erc20_balances(wallet: str, tokens: list[str], chain_id: int) -> dict[str, int]:
    calls = [(token, erc20_abi.encodeABI("balanceOf", [wallet])) for token in tokens]
    results = await multicall3.functions.aggregate3(calls).call()
    return {token: decode_balance(result) for token, result in zip(tokens, results)}
```

**DoD**
- [ ] 20 tokens read in 1 RPC call (not 20 calls)
- [ ] Token with error (e.g. non-ERC20) returns `None` without breaking others

---

#### FEATURE 3.4.3 — `GET /defi/portfolio/{address}/nfts`
**Labels:** `feature` `phase-1` `task-3-4`

**Technical description**
```
GET /api/v1/defi/portfolio/{wallet_address}/nfts?chain_id=1
Response: PaginatedResponse[NFTHolding]
  contract_address, token_id, name, symbol, token_uri, balance (for ERC-1155)
```
Data via `Transfer` event indexer (Epic 5) or third-party API (Alchemy NFT API as fallback).

**DoD**
- [ ] Returns 200 with empty list if no NFTs (not 404)
- [ ] `token_uri` is not resolved by the server (avoid metadata proxying)

---

#### FEATURE 3.4.4 — `GET /defi/portfolio/{address}/defi-positions`
**Labels:** `feature` `phase-1` `task-3-4`

**Technical description**
```
GET /api/v1/defi/portfolio/{wallet_address}/defi-positions?chain_id=1
Response: list[DeFiPosition]
  protocol: "aave-v3" | "uniswap-v3",
  type: "lending" | "borrowing" | "lp",
  assets: list[PositionAsset],
  value_usd: str
```
Via GraphQL subgraph: `https://api.thegraph.com/subgraphs/name/aave/...`

**DoD**
- [ ] Aave V3 positions returned for wallet with active position (integration test)
- [ ] No position returns `[]`, not an error

---

## EPIC 4 — Impersonal Research
**Labels:** `epic` `phase-1` `compliance`  
**Milestone:** F1 – Zero-License MVP

Content published equally to all subscribers. **No personalization by profile, wallet or history.** This boundary is what keeps the module outside the investment advisory regime (RIA/CVM).

**Epic acceptance criteria**
- [ ] No research response contains `user_id`, `wallet_address` or profile-derived data
- [ ] Full-text search functional
- [ ] Rankings updated automatically

---

### TASK 4.1 — Research Content Model
**Labels:** `task` `phase-1` `epic-4`

**Acceptance criteria**
- [ ] `ResearchReport` entity persisted in PostgreSQL
- [ ] FTS with `tsvector` functional
- [ ] Guard prevents publication with `user_id` in payload

---

#### FEATURE 4.1.1 — `ResearchReport` entity
**Labels:** `feature` `phase-1` `task-4-1`  
**File:** `services/defi/domain/entities/research_report.py`

**Technical description**
```python
@dataclass
class ResearchReport:
    report_id: UUID
    title: str              # max 200 chars
    body_markdown: str      # Markdown content
    summary: str            # max 500 chars, generated or manual
    published_at: datetime
    categories: list[str]   # e.g. ["market-analysis", "defi-protocols"]
    tags: list[str]
    version: int            # increments on each edit
    author_type: Literal["editorial", "automated"]  # never "user"
```
**Without fields**: `user_id`, `wallet_address`, `subscriber_id`, `personalized_for`.

**DoD**
- [ ] `ResearchReport` with `user_id` field raises `ValidationError`
- [ ] `author_type` does not accept value `"user"`

---

#### FEATURE 4.1.2 — PostgreSQL repository with FTS
**Labels:** `feature` `phase-1` `task-4-1`  
**File:** `services/defi/infrastructure/persistence/research_repository.py`

**Technical description**  
SQLAlchemy async with `search_vector TSVECTOR` column:
```sql
CREATE INDEX idx_research_fts ON defi_research_reports USING GIN(search_vector);
-- trigger to update search_vector from title + summary + body
```
Search: `WHERE search_vector @@ plainto_tsquery('english', :query)`

**DoD**
- [ ] Keyword search returns relevant reports
- [ ] `tsvector` automatically updated via trigger on insert/update

---

#### FEATURE 4.1.3 — Alembic migration `defi_research_reports`
**Labels:** `feature` `phase-1` `task-4-1`  
**File:** `migrations/defi/`

**Technical description**
```sql
CREATE TABLE defi_research_reports (
  report_id UUID PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  body_markdown TEXT NOT NULL,
  summary VARCHAR(500),
  published_at TIMESTAMPTZ NOT NULL,
  categories TEXT[] DEFAULT '{}',
  tags TEXT[] DEFAULT '{}',
  version INT DEFAULT 1,
  author_type VARCHAR(20) CHECK (author_type IN ('editorial','automated')),
  search_vector TSVECTOR,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_research_fts ON defi_research_reports USING GIN(search_vector);
```

**DoD**
- [ ] `alembic upgrade head` without errors
- [ ] `alembic downgrade -1` reverts without errors

---

#### FEATURE 4.1.4 — Impersonality guard on publication
**Labels:** `feature` `phase-1` `task-4-1` `compliance`  
**File:** `services/defi/domain/research_publisher.py`

**Technical description**  
`ResearchPublisher.publish(report)` verifies:
1. `report.body_markdown` does not contain `{user}`, `{wallet}`, `{portfolio}` personalization placeholders
2. No report field references `user_id` or `wallet_address`
3. Raises `ImpersonalContentViolationError` on violation

**DoD**
- [ ] Report with text `"Recommendation for {user}"` raises error
- [ ] Clean report published successfully

---

### TASK 4.2 — Research API
**Labels:** `task` `phase-1` `epic-4`

**Acceptance criteria**
- [ ] List, detail and search functional
- [ ] HTTP cache with `ETag` functional
- [ ] Search returns results in < 100ms

---

#### FEATURE 4.2.1 — `GET /defi/research`
**Labels:** `feature` `phase-1` `task-4-2`

**Technical description**
```
GET /api/v1/defi/research?category=market-analysis&tag=ethereum&from=2026-01-01&page=1&page_size=10
Response: PaginatedResponse[ResearchSummary]
  report_id, title, summary, published_at, categories, tags
```
**No** `user_id` in query or response.

**DoD**
- [ ] Category and tag filtering functional
- [ ] Response includes `ETag` header for client caching

---

#### FEATURE 4.2.2 — `GET /defi/research/{id}`
**Labels:** `feature` `phase-1` `task-4-2`

**Technical description**
```
GET /api/v1/defi/research/{report_id}
Response 200: ResearchDetailResponse
  report_id, title, body_markdown, summary, published_at, categories, tags, version
Response 404: ErrorResponse
```

**DoD**
- [ ] `body_markdown` returned intact (not processed by server)
- [ ] Header `Cache-Control: public, max-age=300`

---

#### FEATURE 4.2.3 — `GET /defi/research/search`
**Labels:** `feature` `phase-1` `task-4-2`

**Technical description**
```
GET /api/v1/defi/research/search?q=uniswap+liquidity&page=1&page_size=10
Response: PaginatedResponse[ResearchSummary] with extra field `relevance_score: float`
```
Uses `ts_rank(search_vector, plainto_tsquery(:q))` for ordering.

**DoD**
- [ ] Empty query returns 422
- [ ] Results ordered by relevance
- [ ] Unaccented search finds accented text (PostgreSQL `unaccent` config)

---

#### FEATURE 4.2.4 — CDN-friendly HTTP cache
**Labels:** `feature` `phase-1` `task-4-2`  
**File:** `services/defi/api/middleware/cache_headers_middleware.py`

**Technical description**  
Middleware adding headers to research route responses:
- `Cache-Control: public, max-age=300` (5 min for lists and searches)
- `Cache-Control: public, max-age=3600` (1h for individual reports)
- `ETag: "{report_id}-{version}"` for reports
- `Vary: Accept-Encoding`

**DoD**
- [ ] Headers present on all `/defi/research` routes
- [ ] ETag changes when report `version` changes

---

### TASK 4.3 — Public Rankings
**Labels:** `task` `phase-1` `epic-4`

**Acceptance criteria**
- [ ] Protocol and chain rankings available
- [ ] Automatic update every 15 min
- [ ] No user personalization

---

#### FEATURE 4.3.1 — `GET /defi/research/rankings/protocols`
**Labels:** `feature` `phase-1` `task-4-3`

**Technical description**
```
GET /api/v1/defi/research/rankings/protocols?metric=tvl&limit=20
Response: list[ProtocolRanking]
  rank, protocol_name, chain, tvl_usd, volume_24h_usd, fees_24h_usd, change_7d_pct
```
Data from DeFiLlama (see Feature 2.3.4). Cached in Redis with 15 min TTL.

**DoD**
- [ ] Returns data even if DeFiLlama is temporarily unavailable (stale cache)

---

#### FEATURE 4.3.2 — `GET /defi/research/rankings/chains`
**Labels:** `feature` `phase-1` `task-4-3`

**Technical description**
```
GET /api/v1/defi/research/rankings/chains
Response: list[ChainRanking]
  rank, chain_name, chain_id, tvl_usd, tps_avg, avg_gas_fee_usd, active_addresses_24h
```

**DoD**
- [ ] At least Ethereum, Polygon, Arbitrum, Base returned

---

#### FEATURE 4.3.3 — Research rankings refresh worker
**Labels:** `feature` `phase-1` `task-4-3` `infra`

**Technical description**  
Reuse `refresh_rankings` task from Feature 2.3.5 adding research rankings update. Cron every 15 min via ARQ scheduler.

**DoD**
- [ ] Rankings never return data older than 30 minutes

---

## EPIC 5 — Off-Chain Infrastructure
**Labels:** `epic` `phase-1` `infra`  
**Milestone:** F1 – Zero-License MVP

Workers, queues, on-chain event indexer and reconciliation. Infrastructure supporting Epics 2, 3 and 4 without custodying funds — reads only public blockchain state.

**Epic acceptance criteria**
- [ ] Transaction confirmation worker operational
- [ ] Indexer processes new blocks with < 30s lag
- [ ] Reorg detected and affected events marked as `orphaned`
- [ ] Worker health check available at `GET /health`

---

### TASK 5.1 — Async Workers
**Labels:** `task` `phase-1` `epic-5` `infra`

**Acceptance criteria**
- [ ] Workers start via `docker-compose` without errors
- [ ] Idempotency: same task executed twice does not generate duplicate
- [ ] DLQ receives tasks after 3 failures

---

#### FEATURE 5.1.1 — ARQ setup for DeFi context
**Labels:** `feature` `phase-1` `task-5-1`  
**File:** `services/defi/infrastructure/workers/worker_settings.py`

**Technical description**
```python
class WorkerSettings:
    functions = [confirm_transaction, update_prices, index_events, refresh_rankings, reconcile_balances]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    queue_name = "defi"
    max_jobs = 10
    job_timeout = 300  # 5 min
    health_check_interval = 30
```
Add entry to `docker-compose.yml`:
```yaml
defi-worker:
  command: python -m arq services.defi.infrastructure.workers.worker_settings.WorkerSettings
```

**DoD**
- [ ] `docker-compose up defi-worker` starts without errors
- [ ] `GET /api/v1/defi/health` includes worker status

---

#### FEATURE 5.1.2 — Task definitions
**Labels:** `feature` `phase-1` `task-5-1`  
**File:** `services/defi/infrastructure/workers/tasks.py`

**Technical description**
```python
async def confirm_transaction(ctx, tx_hash: str, webhook_url: str | None = None): ...
async def update_prices(ctx, symbols: list[str]): ...
async def index_events(ctx, from_block: int, to_block: int): ...
async def refresh_rankings(ctx): ...
async def reconcile_balances(ctx, wallet_address: str): ...
```
Each task receives `ctx` with `redis` and injected services.

**DoD**
- [ ] Each task has individual timeout configured
- [ ] Tasks log start and end with `task_id` for traceability

---

#### FEATURE 5.1.3 — Worker idempotency layer
**Labels:** `feature` `phase-1` `task-5-1`  
**File:** `services/defi/infrastructure/workers/idempotency.py`

**Technical description**
```python
async def is_already_running(redis, task_name: str, key: str) -> bool:
    return await redis.set(f"defi:task:{task_name}:{key}", "1", nx=True, ex=300) is None
```
Each task checks at the start if it is already running for the same `key` (e.g. `tx_hash` for `confirm_transaction`).

**DoD**
- [ ] Second queuing of `confirm_transaction` with same `tx_hash` does not process duplicate
- [ ] Lock automatically releases in 5 min (TTL)

---

#### FEATURE 5.1.4 — DLQ and retry policy
**Labels:** `feature` `phase-1` `task-5-1`

**Technical description**  
Configure in `WorkerSettings`:
```python
retry_jobs = True
max_tries = 3
# ARQ uses exponential backoff by default: 1s, 2s, 4s
```
Tasks reaching `max_tries` moved to queue `defi:dlq` in Redis with full payload for analysis.

**DoD**
- [ ] After 3 failures, task appears in `defi:dlq`
- [ ] Monitoring alert fired when DLQ is not empty

---

#### FEATURE 5.1.5 — Worker health check
**Labels:** `feature` `phase-1` `task-5-1`

**Technical description**  
Extend `GET /api/v1/defi/health` to include:
```json
{
  "status": "ok",
  "components": {
    "worker": "ok",
    "redis": "ok",
    "market_data_provider": "ok",
    "indexer_lag_blocks": 3
  }
}
```
Worker exposes heartbeat in Redis: `defi:worker:heartbeat` with 60s TTL. Health check verifies if key exists.

**DoD**
- [ ] Stopped worker causes `"worker": "down"` within 60s
- [ ] `indexer_lag_blocks > 10` changes `status` to `"degraded"`

---

### TASK 5.2 — On-Chain Indexer
**Labels:** `task` `phase-1` `epic-5` `blockchain` `infra`

**Acceptance criteria**
- [ ] Indexer processes ERC-20 Transfer events from finalized blocks
- [ ] Lag < 30s under normal conditions
- [ ] Reorg detected and handled

---

#### FEATURE 5.2.1 — `BlockListener`
**Labels:** `feature` `phase-1` `task-5-2`  
**File:** `services/defi/infrastructure/indexer/block_listener.py`

**Technical description**
```python
class BlockListener:
    async def start(self):
        # web3.eth.filter("latest") for websocket
        # or polling: while True: await process_block(web3.eth.block_number)
    async def process_block(self, block_number: int): ...
    async def stop(self): ...
```
Persists `last_indexed_block` in Redis for resumption after restart.

**DoD**
- [ ] Resumes from last indexed block after restart
- [ ] Does not process the same block twice (idempotency)

---

#### FEATURE 5.2.2 — ERC-20 Transfer event indexer
**Labels:** `feature` `phase-1` `task-5-2`  
**File:** `services/defi/infrastructure/indexer/erc20_transfer_indexer.py`

**Technical description**
```python
TRANSFER_TOPIC = web3.keccak(text="Transfer(address,address,uint256)").hex()

async def index_block(self, block_number: int):
    logs = await web3.eth.get_logs({
        "fromBlock": block_number, "toBlock": block_number,
        "topics": [TRANSFER_TOPIC]
    })
    for log in logs:
        await self.save_event(log)
```

**DoD**
- [ ] Events persisted in `defi_indexed_events` with `block`, `tx_hash`, `event_type`, `from`, `to`, `amount`, `token_address`, `indexed_at`
- [ ] `indexed_at` is local timestamp (when indexed), distinct from `block_timestamp`

---

#### FEATURE 5.2.3 — Uniswap V2/V3 event indexer
**Labels:** `feature` `phase-1` `task-5-2`  
**File:** `services/defi/infrastructure/indexer/uniswap_event_indexer.py`

**Technical description**  
Topics:
- V2 Swap: `keccak("Swap(address,uint256,uint256,uint256,uint256,address)")`
- V3 Swap: `keccak("Swap(address,address,int256,int256,uint160,uint128,int24)")`

**DoD**
- [ ] Swaps indexed with `pair_address`, `token0`, `token1`, `amount0`, `amount1`

---

#### FEATURE 5.2.4 — Schema and migration `defi_indexed_events`
**Labels:** `feature` `phase-1` `task-5-2`

**Technical description**
```sql
CREATE TABLE defi_indexed_events (
  id BIGSERIAL PRIMARY KEY,
  block_number BIGINT NOT NULL,
  tx_hash VARCHAR(66) NOT NULL,
  log_index INT NOT NULL,
  event_type VARCHAR(50) NOT NULL,     -- Transfer, Swap, Mint, Burn
  contract_address VARCHAR(42) NOT NULL,
  from_address VARCHAR(42),
  to_address VARCHAR(42),
  raw_args JSONB NOT NULL,
  chain_id INT NOT NULL,
  status VARCHAR(20) DEFAULT 'confirmed',  -- confirmed, orphaned
  indexed_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(tx_hash, log_index, chain_id)
);
CREATE INDEX idx_events_from ON defi_indexed_events(from_address, chain_id);
CREATE INDEX idx_events_to ON defi_indexed_events(to_address, chain_id);
CREATE INDEX idx_events_block ON defi_indexed_events(block_number, chain_id);
```

**DoD**
- [ ] `alembic upgrade head` without errors
- [ ] `UNIQUE(tx_hash, log_index, chain_id)` constraint prevents duplicates

---

#### FEATURE 5.2.5 — Indexer lag monitor
**Labels:** `feature` `phase-1` `task-5-2`

**Technical description**  
In `application/indexer_health_service.py`:
```python
async def get_lag(self, chain_id: int) -> int:
    current_block = await web3.eth.block_number
    last_indexed = await redis.get(f"defi:indexer:last_block:{chain_id}")
    return current_block - int(last_indexed)
```
If `lag > 10`, raises `IndexerLagError` and changes `health.status` to `"degraded"`.

**DoD**
- [ ] Health check reflects lag in real time
- [ ] Alert generated if lag > 50 blocks

---

### TASK 5.3 — Reconciliation and Data Integrity
**Labels:** `task` `phase-1` `epic-5` `infra`

**Acceptance criteria**
- [ ] Reorg detected within 1 block distance
- [ ] Orphaned block events marked as `orphaned` (not deleted)
- [ ] Balance reconciliation runs hourly

---

#### FEATURE 5.3.1 — Balance reconciliation worker
**Labels:** `feature` `phase-1` `task-5-3`  
**File:** `services/defi/infrastructure/workers/reconciliation_worker.py`

**Technical description**  
Task `reconcile_balances(wallet_address)`:
1. Calculates ERC-20 balance from `defi_indexed_events` (sum of transfers)
2. Verifies via `eth_call` the actual on-chain balance
3. If divergence > 0.01%, records alert in `defi_reconciliation_alerts`

**DoD**
- [ ] Divergence detected when Transfer event is missing from index
- [ ] No divergence: no alert generated

---

#### FEATURE 5.3.2 — Reorg detector
**Labels:** `feature` `phase-1` `task-5-3`  
**File:** `services/defi/infrastructure/indexer/reorg_detector.py`

**Technical description**  
On each new block:
```python
prev_stored_hash = await get_stored_block_hash(block_number - 1)
actual_parent_hash = new_block.parentHash.hex()
if prev_stored_hash != actual_parent_hash:
    await handle_reorg(from_block=find_common_ancestor(), to_block=block_number - 1)
```
`handle_reorg`: marks events of affected blocks as `status = 'orphaned'`, re-indexes from common ancestor.

**DoD**
- [ ] 1-block reorg detected and handled in unit test with mocked web3
- [ ] `orphaned` events do not appear in portfolio queries

---

#### FEATURE 5.3.3 — Lost block recovery
**Labels:** `feature` `phase-1` `task-5-3`

**Technical description**  
On `BlockListener` startup:
```python
last_indexed = await redis.get("defi:indexer:last_block:1")
current = await web3.eth.block_number
if current - last_indexed > 1:
    await enqueue_task("index_events", from_block=last_indexed+1, to_block=current)
```

**DoD**
- [ ] Gap of 100 blocks (simulating downtime) recovered automatically
- [ ] Blocks processed in ascending order

---

## EPIC 6 — Compliance and Non-Custodial Guards
**Labels:** `epic` `phase-1` `compliance`  
**Milestone:** F1 – Zero-License MVP

Implements the remaining obligations from the architecture document: OFAC screening, technical guards that make non-custody verifiable by code, immutable audit trail and ToU.

**Epic acceptance criteria**
- [ ] Sanctioned address blocked before any processing
- [ ] No module in `services/defi/` signs a transaction on the server (verified by AST test)
- [ ] Immutable audit log recorded for every DeFi API call
- [ ] User without accepted ToU cannot access DeFi endpoints

---

### TASK 6.1 — OFAC / Sanctions Screening
**Labels:** `task` `phase-1` `epic-6` `compliance`

**Acceptance criteria**
- [ ] Address on OFAC SDN list returns 403 on any DeFi endpoint
- [ ] Screening result logged with hashed address (not plain text)
- [ ] Screening does not block requests by more than 50ms (clean address cache)

---

#### FEATURE 6.1.1 — Sanctions screening API integration
**Labels:** `feature` `phase-1` `task-6-1`  
**File:** `services/defi/infrastructure/compliance/sanctions_checker.py`

**Technical description**  
Implement `ISanctionsChecker` with two configurable options:
- **Option A (paid)**: TRM Labs API — `POST /v1/risk/address` with `{ "address": "0x..." }`
- **Option B (free)**: Periodic download of OFAC SDN list (`sdn.xml`) and local check against extracted ETH addresses

For MVP: use Option B. Cache clean addresses in Redis for 24h (`defi:sanctions:clean:{address_hash}` = `"1"`).

**Implementation notes**
- Hash address with `sha256` for log storage (not plain text)
- `check(address)` returns `SanctionsResult(is_sanctioned: bool, source: str, checked_at: datetime)`

**DoD**
- [ ] Address `0x7F367cC41522cE07553e823bf3be79A889DEbe1B` (Tornado Cash — OFAC) returns `is_sanctioned=True`
- [ ] Cache avoids API call for recently verified address
- [ ] Unit tests with mocked SDN list

---

#### FEATURE 6.1.2 — Sanctions screening middleware
**Labels:** `feature` `phase-1` `task-6-1` `compliance`  
**File:** `services/defi/api/middleware/sanctions_guard.py`

**Technical description**  
`BaseHTTPMiddleware` extracting `wallet_address` from:
- Path params (e.g. `/portfolio/{wallet_address}/...`)
- Request body (`wallet_address` or `to` fields in transactions)
- Header `X-Wallet-Address`

If address found and `is_sanctioned=True`: returns HTTP 403:
```json
{"error_code": "sanctioned_address", "message": "Access denied."}
```
**Without** revealing why the address was blocked.

**DoD**
- [ ] Request with OFAC address returns 403
- [ ] Request without address passes normally
- [ ] Error message does not mention "OFAC" or "sanctions" (avoid informing the offender)

---

#### FEATURE 6.1.3 — Jurisdiction blocking
**Labels:** `feature` `phase-1` `task-6-1` `compliance`  
**File:** `services/defi/domain/compliance/jurisdiction_blocklist.py`

**Technical description**  
List of blocked country codes per OFAC country programs (Cuba, Iran, North Korea, Syria, Russia-specific, Crimea):
```python
BLOCKED_COUNTRIES = frozenset(["CU", "IR", "KP", "SY", "RU"])  # illustrative; review with legal counsel
```
Check based on request IP (via `X-Forwarded-For` or Cloudflare `CF-IPCountry` header).

**DoD**
- [ ] IP from blocked country returns 451 (`Unavailable For Legal Reasons`)
- [ ] VPN is not the platform's responsibility (document in ToU)
- [ ] List updatable via configuration without redeploy

---

#### FEATURE 6.1.4 — Screening audit log
**Labels:** `feature` `phase-1` `task-6-1` `compliance`  
**File:** `services/defi/infrastructure/compliance/audit_logger.py`

**Technical description**  
Record in `defi_sanctions_log`:
```sql
address_hash VARCHAR(64),   -- sha256 of address
result VARCHAR(10),         -- pass | block
source VARCHAR(50),         -- ofac_sdnlist | trm_labs
checked_at TIMESTAMPTZ,
request_id VARCHAR(36)
```
**Never** store address in plain text in this table.

**DoD**
- [ ] Table is `INSERT`-only in the application (no UPDATE/DELETE)
- [ ] `address_hash` verifiable: `sha256("0x{address_lower}")` = stored value

---

### TASK 6.2 — Non-Custodial Technical Guards
**Labels:** `task` `phase-1` `epic-6` `compliance`

**Acceptance criteria**
- [ ] Payload with `private_key` returns 422 on any DeFi endpoint
- [ ] AST test passes ensuring `sign_transaction` is not called on the server
- [ ] Billing isolated from transaction flow (verified by test)

---

#### FEATURE 6.2.1 — `NonCustodialGuard` middleware
**Labels:** `feature` `phase-1` `task-6-2` `compliance`

*(See Feature 3.2.5 — same deliverable; registered here as compliance reference)*  
Ensure the middleware is active on **all** `/api/v1/defi/` routes, not just transaction routes.

**DoD**
- [ ] Middleware applied at the `defi_router` level, not route by route

---

#### FEATURE 6.2.2 — Signing guardrail in `TransactionBuilderService`
**Labels:** `feature` `phase-1` `task-6-2` `compliance`

**Technical description**  
Inside `TransactionBuilderService.build()`, after building the tx:
```python
if hasattr(result, 'v') or hasattr(result, 'signature'):
    raise NonCustodialViolationError(violation_type="server_signed_transaction")
```
Also: the service must not import `eth_account` — if ABI encoding is needed, use `web3.py` only.

**DoD**
- [ ] `eth_account` not imported in any `services/defi/` file
- [ ] Verified by AST test

---

#### FEATURE 6.2.3 — Non-custody AST architecture test
**Labels:** `feature` `phase-1` `task-6-2` `compliance`  
**File:** `tests/defi/test_arch_non_custodial.py`

**Technical description**
```python
import ast, pathlib

def test_no_sign_transaction_in_defi():
    for py_file in pathlib.Path("services/defi").rglob("*.py"):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "sign_transaction":
                pytest.fail(f"sign_transaction found in {py_file}")

def test_no_eth_account_import():
    for py_file in pathlib.Path("services/defi").rglob("*.py"):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "eth_account" not in alias.name, f"eth_account imported in {py_file}"
```

**DoD**
- [ ] Test runs in `pytest` and passes with current code
- [ ] Adding `from eth_account import Account` to any DeFi file breaks the test

---

#### FEATURE 6.2.4 — Billing isolation test
**Labels:** `feature` `phase-1` `task-6-2` `compliance`  
**File:** `tests/defi/test_arch_billing_isolation.py`

**Technical description**  
AST scan verifying no file in `services/defi/` imports billing modules from the main platform (e.g. `app.billing`, `app.payments`, `stripe`).

**DoD**
- [ ] Any billing import in `services/defi/` breaks the test

---

### TASK 6.3 — Audit Trail
**Labels:** `task` `phase-1` `epic-6` `compliance`

**Acceptance criteria**
- [ ] Each authenticated DeFi API call generates 1 record in `defi_audit_log`
- [ ] Table does not allow UPDATE or DELETE from the application
- [ ] Archival worker functional

---

#### FEATURE 6.3.1 — `AuditLogger` middleware
**Labels:** `feature` `phase-1` `task-6-3`  
**File:** `services/defi/infrastructure/audit/audit_logger.py`

**Technical description**  
`BaseHTTPMiddleware` recording asynchronously (background task):
```python
class AuditEntry:
    request_id: UUID
    user_id: str | None
    wallet_address: str | None  # public address only
    endpoint: str               # e.g. "POST /api/v1/defi/transactions/broadcast"
    method: str
    payload_hash: str           # sha256 of body (not the body itself)
    ip_address: str
    response_status: int
    duration_ms: int
    timestamp: datetime
```
**Do not** store full body — hash only.

**DoD**
- [ ] Record created for every authenticated request
- [ ] `payload_hash` reproducible: `sha256(body_bytes)` = stored value
- [ ] Does not block response (log in background task)

---

#### FEATURE 6.3.2 — Immutable `defi_audit_log` table
**Labels:** `feature` `phase-1` `task-6-3`  
**File:** `migrations/defi/`

**Technical description**
```sql
CREATE TABLE defi_audit_log (
  id BIGSERIAL PRIMARY KEY,
  request_id UUID NOT NULL,
  user_id VARCHAR(100),
  wallet_address VARCHAR(42),
  endpoint VARCHAR(200) NOT NULL,
  method VARCHAR(10) NOT NULL,
  payload_hash VARCHAR(64),
  ip_address VARCHAR(45),
  response_status INT,
  duration_ms INT,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Revoke UPDATE and DELETE from the application role:
REVOKE UPDATE, DELETE ON defi_audit_log FROM app_role;
```

**DoD**
- [ ] `UPDATE defi_audit_log SET ...` fails with permission denied for app role
- [ ] `SELECT` works normally
- [ ] Index on `(wallet_address, timestamp)` for audit queries

---

#### FEATURE 6.3.3 — Log archival worker
**Labels:** `feature` `phase-1` `task-6-3` `infra`  
**File:** `services/defi/infrastructure/workers/log_archival_worker.py`

**Technical description**  
Task `archive_audit_logs` executed monthly:
1. Selects records with `timestamp < NOW() - INTERVAL '7 years'`
2. Exports to compressed NDJSON (gzip)
3. Uploads to S3/GCS with path `audit-archive/{year}/{month}/defi_audit_log.ndjson.gz`
4. Deletes archived records from PostgreSQL

**DoD**
- [ ] Archive generated correctly with all fields
- [ ] Deletion only occurs after successful upload confirmation

---

#### FEATURE 6.3.4 — `GET /internal/defi/audit`
**Labels:** `feature` `phase-1` `task-6-3`

**Technical description**
```
GET /api/v1/internal/defi/audit?wallet=0x...&from=2026-01-01&to=2026-02-01&page=1
Header: X-Admin-Key: {admin_api_key}
Response: PaginatedResponse[AuditEntry]
```
Authenticated by admin API key (not user JWT). Restricted to internal IPs when possible.

**DoD**
- [ ] Without `X-Admin-Key` returns 401
- [ ] Invalid `X-Admin-Key` returns 401 (not 403, to avoid revealing the route exists)

---

### TASK 6.4 — Terms of Use
**Labels:** `task` `phase-1` `epic-6` `compliance`

**Acceptance criteria**
- [ ] User without accepted ToU receives 403 on any DeFi endpoint
- [ ] Acceptance recorded with timestamp and version
- [ ] New major version forces re-acceptance

---

#### FEATURE 6.4.1 — `ToUService`
**Labels:** `feature` `phase-1` `task-6-4`  
**File:** `services/defi/application/tou_service.py`

**Technical description**
```python
class ToUService:
    async def get_current_version(self) -> TermsOfUse: ...
    async def has_accepted(self, user_id: str) -> bool: ...
    async def accept(self, user_id: str, version: str, ip: str) -> None: ...
    async def requires_reaccept(self, user_id: str) -> bool:
        # True if accepted version < current version with different major
```

**DoD**
- [ ] `has_accepted` returns `False` for user with no record
- [ ] Unit tests covering ToU versioning

---

#### FEATURE 6.4.2 — `ToUCheckMiddleware`
**Labels:** `feature` `phase-1` `task-6-4` `compliance`  
**File:** `services/defi/api/middleware/tou_middleware.py`

**Technical description**  
Applied to all `/api/v1/defi/` routes except `GET /defi/health` and `POST /defi/terms/accept`:
```python
if not await tou_service.has_accepted(user_id):
    return JSONResponse(
        status_code=403,
        content={"error_code": "tou_required", "accept_url": "/api/v1/defi/terms/accept"}
    )
```

**DoD**
- [ ] New user receives 403 with `tou_required` on first DeFi call
- [ ] After accepting, next call passes normally

---

#### FEATURE 6.4.3 — `POST /defi/terms/accept`
**Labels:** `feature` `phase-1` `task-6-4`

**Technical description**
```
POST /api/v1/defi/terms/accept
Header: Authorization: Bearer {jwt}
Body: { "version": "1.0", "accepted": true }
Response 200: { "accepted_at": "2026-05-31T...", "version": "1.0" }
Response 422: { "error_code": "must_accept_true" }  // if accepted=false
```
Persists in `defi_tou_acceptances(user_id, version, accepted_at, ip_address)`.

**DoD**
- [ ] `accepted: false` returns 422
- [ ] Accepting an old version when a newer exists returns 409 with current version
- [ ] Record immutable (no UPDATE/DELETE from application)

---

#### FEATURE 6.4.4 — Versioning and `requires_reaccept`
**Labels:** `feature` `phase-1` `task-6-4`  
**File:** `services/defi/domain/entities/terms_of_use.py`

**Technical description**
```python
@dataclass
class TermsOfUse:
    version: str         # semver: "1.0", "1.1", "2.0"
    published_at: datetime
    requires_reaccept: bool  # True for major versions (x.0)
    content_url: str
```
Rule: `requires_reaccept = True` if `int(version.split(".")[0]) > int(previous.split(".")[0])`.

**DoD**
- [ ] Upgrade `1.0 → 1.1` does not require re-acceptance
- [ ] Upgrade `1.1 → 2.0` requires re-acceptance
- [ ] Unit tests for versioning rule

---

## EPIC 7 — Generic Tokenization Tooling (Phase 2)
**Labels:** `epic` `phase-2` `blockchain`  
**Milestone:** F2 – Tokenization  
**⚠️ Blocked by:** Prior legal validation (confirm "neutral tool" framing with capital markets attorney)

The client is the issuer and responsible party. The platform provides audited templates and builds unsigned transactions. The server is **never** `msg.sender` and never signs deployments.

**Epic acceptance criteria**
- [ ] ERC-20 deploy via audited template functional on testnet
- [ ] Server never is `msg.sender` — client signs the deploy
- [ ] All templates with passing Foundry suite + Slither
- [ ] Legal validation documented and archived before enabling in production

---

### TASK 7.1 — Smart Contract Template Library
**Labels:** `task` `phase-2` `epic-7` `blockchain`

**Acceptance criteria**
- [ ] ERC-20, ERC-721 and ERC-1155 factory templates compile without warnings
- [ ] Foundry tests passing with coverage > 90%
- [ ] Slither without High or Critical severity findings

---

#### FEATURE 7.1.1 — Audited ERC-20 factory template
**Labels:** `feature` `phase-2` `task-7-1`  
**File:** `contracts/templates/ERC20Factory.sol`

**Technical description**  
Based on OpenZeppelin `ERC20`, `ERC20Burnable`, `ERC20Mintable`:
```solidity
contract ERC20Factory {
    event TokenDeployed(address indexed token, address indexed deployer);

    function deploy(
        string memory name, string memory symbol,
        uint256 initialSupply, uint8 decimals,
        bool mintable, bool burnable,
        address owner  // always msg.sender — never platform address
    ) external returns (address) { ... }
}
```
`owner` must be `msg.sender` — validation `require(owner == msg.sender)`.

**Implementation notes**
- Use Solidity `^0.8.20`
- Inherit from OpenZeppelin contracts (do not re-implement ERC-20 from scratch)
- `owner` receives `DEFAULT_ADMIN_ROLE` from `AccessControl`

**DoD**
- [ ] `forge build` without warnings
- [ ] `owner != msg.sender` reverts with `"owner must be deployer"`
- [ ] ABI exported for use in Python adapter

---

#### FEATURE 7.1.2 — Audited ERC-721 factory template
**Labels:** `feature` `phase-2` `task-7-1`  
**File:** `contracts/templates/ERC721Factory.sol`

**Technical description**  
Parameters: `name`, `symbol`, `baseURI`, `maxSupply` (0 = unlimited), `owner`.  
Function `safeMint(address to, uint256 tokenId)` for `owner` only.

**DoD**
- [ ] Mint by non-owner reverts
- [ ] `maxSupply > 0` causes `safeMint` beyond limit to revert

---

#### FEATURE 7.1.3 — Audited ERC-1155 factory template
**Labels:** `feature` `phase-2` `task-7-1`  
**File:** `contracts/templates/ERC1155Factory.sol`

**Technical description**  
Parameters: `uri` (base URI), `owner`.  
`mint(address to, uint256 id, uint256 amount, bytes data)` for `owner` only.

**DoD**
- [ ] `forge build` without warnings
- [ ] Foundry fuzz test: `mint` with `amount=0` does not emit Transfer event

---

#### FEATURE 7.1.4 — Template versioning
**Labels:** `feature` `phase-2` `task-7-1`  
**File:** `services/defi/domain/entities/contract_template.py`

**Technical description**
```python
@dataclass(frozen=True)
class ContractTemplate:
    template_id: str              # e.g. "erc20-v1"
    version: str                  # semver
    standard: Literal["ERC20","ERC721","ERC1155"]
    bytecode: str                 # compiled bytecode hex
    abi: list[dict]
    audit_report_url: str         # mandatory — without URL, template cannot be used
    is_active: bool               # only active templates can be deployed
```
The platform only permits deployment of templates with `is_active=True` and `audit_report_url != ""`.

**DoD**
- [ ] Template without `audit_report_url` cannot be marked `is_active=True`
- [ ] Unit tests for the validation

---

#### FEATURE 7.1.5 — Template parameter validation
**Labels:** `feature` `phase-2` `task-7-1`  
**File:** `services/defi/domain/validators/template_validator.py`

**Technical description**  
For ERC-20: `name` (1–50 chars), `symbol` (1–11 chars, uppercase), `initial_supply > 0`, `decimals` (0–18).  
For ERC-721: `name` (1–50 chars), `symbol` (1–11 chars), `max_supply >= 0`.

**DoD**
- [ ] `symbol = ""` raises `ValidationError`
- [ ] `decimals = 19` raises `ValidationError`
- [ ] Tests covering all limits

---

### TASK 7.2 — Token Deployment Flow
**Labels:** `task` `phase-2` `epic-7`

**Acceptance criteria**
- [ ] `POST /defi/tokenization/deploy/estimate` returns unsigned deploy tx
- [ ] `msg.sender` of deploy is always the client — server never acts as deployer
- [ ] Contract registered locally after confirmation

---

#### FEATURE 7.2.1 — `TokenizationService`
**Labels:** `feature` `phase-2` `task-7-2`  
**File:** `services/defi/application/tokenization_service.py`

**Technical description**
```python
class TokenizationService:
    async def estimate_deploy(
        self, template_id: str, params: dict, deployer_address: str, chain_id: int
    ) -> UnsignedTransaction:
        template = await self.template_repo.get_active(template_id)
        encoded_constructor = encode_constructor(template.abi, params, deployer_address)
        bytecode_with_args = template.bytecode + encoded_constructor
        return UnsignedTransaction(
            to=None,  # deploy: to=None
            data=bytecode_with_args,
            value=0,
            ...
        )
```
`deployer_address` comes from the user's `WalletSession` — never from an unauthenticated external argument.

**DoD**
- [ ] `to=None` in deploy `UnsignedTransaction`
- [ ] `NonCustodialViolationError` if `deployer_address` is the company's address

---

#### FEATURE 7.2.2 — `POST /defi/tokenization/deploy/estimate`
**Labels:** `feature` `phase-2` `task-7-2`

**Technical description**
```
POST /api/v1/defi/tokenization/deploy/estimate
Header: Authorization: Bearer {session_token}
Body: {
  "template_id": "erc20-v1",
  "params": { "name": "MyToken", "symbol": "MTK", "initial_supply": "1000000", "decimals": 18, "mintable": true, "burnable": false }
}
Response 200: {
  "unsigned_tx": { "to": null, "data": "0x...", "value": "0", "nonce": 5, ... },
  "estimated_gas": 1500000,
  "estimated_fee_usd": "12.50",
  "template_id": "erc20-v1",
  "template_version": "1.0"
}
```

**DoD**
- [ ] Response includes `template_id` and `template_version` so the client knows what they are deploying
- [ ] Inactive template returns 422

---

#### FEATURE 7.2.3 — Guard: client as deployer
**Labels:** `feature` `phase-2` `task-7-2` `compliance`

**Technical description**  
In `TokenizationService.estimate_deploy()`:
```python
COMPANY_ADDRESSES = frozenset({settings.company_hot_wallet, settings.company_treasury})
if deployer_address.lower() in {a.lower() for a in COMPANY_ADDRESSES}:
    raise NonCustodialViolationError(violation_type="company_as_deployer")
```

**DoD**
- [ ] Company address as `deployer` raises `NonCustodialViolationError`
- [ ] Unit test verifying the guard

---

#### FEATURE 7.2.4 — `POST /defi/tokenization/deploy/confirm`
**Labels:** `feature` `phase-2` `task-7-2`

**Technical description**
```
POST /api/v1/defi/tokenization/deploy/confirm
Body: { "tx_hash": "0x...", "chain_id": 1 }
Response 200: {
  "contract_address": "0x...",
  "template_id": "erc20-v1",
  "deployer": "0x...",
  "chain_id": 1,
  "block_number": 19000000
}
```
Verifies receipt on-chain and extracts `contractAddress` from receipt. Persists in `defi_deployed_contracts`.

**DoD**
- [ ] `contract_address` extracted from receipt (not from body — avoids spoofing)
- [ ] `tx_hash` not found returns 404

---

#### FEATURE 7.2.5 — `GET /defi/tokenization/contracts/{address}`
**Labels:** `feature` `phase-2` `task-7-2`

**Technical description**
```
GET /api/v1/defi/tokenization/contracts/{contract_address}
Response 200: {
  "contract_address": "0x...", "template_id": "erc20-v1", "template_version": "1.0",
  "deployer": "0x...", "chain_id": 1, "deployed_at": "2026-06-01T...",
  "tx_hash": "0x..."
}
```

**DoD**
- [ ] Unregistered address returns 404
- [ ] Does not expose subscriber data beyond deployer's public address

---

### TASK 7.3 — Token Management Tools
**Labels:** `task` `phase-2` `epic-7`

**Acceptance criteria**
- [ ] Mint/burn/transfer return unsigned tx
- [ ] Metadata read via `eth_call` (read-only)

---

#### FEATURE 7.3.1 — `POST /defi/tokenization/{address}/mint/estimate`
**Labels:** `feature` `phase-2` `task-7-3`

**Technical description**
```
POST /api/v1/defi/tokenization/{contract_address}/mint/estimate
Body: { "to": "0x...", "amount": "1000" }
Response 200: UnsignedTransaction (mint calldata)
```
Using `contract.encodeABI("mint", [to, amount])` via `web3.py`.

**DoD**
- [ ] `amount <= 0` returns 422
- [ ] Unregistered contract returns 404

---

#### FEATURE 7.3.2 — `POST /defi/tokenization/{address}/burn/estimate`
**Labels:** `feature` `phase-2` `task-7-3`

**Technical description**
```
POST /api/v1/defi/tokenization/{contract_address}/burn/estimate
Body: { "amount": "500" }
Response 200: UnsignedTransaction (burn calldata)
```

**DoD**
- [ ] Correct calldata for `burn(uint256)`
- [ ] Template without `burnable=true` returns 422

---

#### FEATURE 7.3.3 — `POST /defi/tokenization/{address}/transfer/estimate`
**Labels:** `feature` `phase-2` `task-7-3`

*(Reuses Feature 3.2.3 — ERC-20 Builder)*  
Expose specific endpoint for tokens deployed via the platform.

**DoD**
- [ ] Same behavior as generic ERC-20 builder
- [ ] Unregistered contract returns 404

---

#### FEATURE 7.3.4 — `GET /defi/tokenization/{address}/metadata`
**Labels:** `feature` `phase-2` `task-7-3`

**Technical description**
```
GET /api/v1/defi/tokenization/{contract_address}/metadata
Response 200: {
  "name": "MyToken", "symbol": "MTK", "decimals": 18,
  "total_supply": "1000000", "owner": "0x...", "standard": "ERC20"
}
```
Via `web3.eth.call` — no write operations.

**DoD**
- [ ] Data read on-chain in real time (not from local registry)
- [ ] Non-ERC20 contract returns a clear error

---

### TASK 7.4 — Contract Testing and Audit Pipeline
**Labels:** `task` `phase-2` `epic-7` `infra`

**Acceptance criteria**
- [ ] `forge test` passes with coverage > 90%
- [ ] Slither without High/Critical findings
- [ ] CI blocks PR if unaudited contract is added

---

#### FEATURE 7.4.1 — Foundry suite for all templates
**Labels:** `feature` `phase-2` `task-7-4`  
**File:** `contracts/test/`

**Technical description**  
For each template:
- Unit tests: deploy, mint, burn, transfer, access control
- Fuzz tests: `testFuzz_mint(address to, uint256 amount)` with `vm.assume()`
- Invariant tests: `totalSupply == sum(balances)` always holds

**DoD**
- [ ] `forge test -vv` passes without failures
- [ ] `forge coverage` reports > 90% line coverage

---

#### FEATURE 7.4.2 — CI for contracts
**Labels:** `feature` `phase-2` `task-7-4`  
**File:** `.github/workflows/contracts.yml`

**Technical description**
```yaml
on:
  pull_request:
    paths: ["contracts/**"]
jobs:
  test:
    steps:
      - uses: foundry-rs/foundry-toolchain@v1
      - run: forge test
      - run: forge coverage --report lcov
```

**DoD**
- [ ] PR touching `contracts/` mandatorily runs the tests
- [ ] Coverage report published as CI artifact

---

#### FEATURE 7.4.3 — Slither in CI
**Labels:** `feature` `phase-2` `task-7-4`

**Technical description**
```yaml
- name: Slither Analysis
  uses: crytic/slither-action@v0.3.0
  with:
    fail-on: high
```
Low/Medium findings are reported but do not block. High/Critical block the merge.

**DoD**
- [ ] CI fails if Slither finds `High` or `Critical` finding
- [ ] Low and Medium severity findings listed as PR comment

---

#### FEATURE 7.4.4 — Gas report
**Labels:** `feature` `phase-2` `task-7-4`

**Technical description**
```yaml
- run: forge snapshot
- run: git diff .gas-snapshot
```
`forge snapshot` generates committed `.gas-snapshot`. PRs show gas regression diff.

**DoD**
- [ ] `.gas-snapshot` committed in the repo
- [ ] PR increasing ERC-20 deploy gas by > 5% triggers CI warning

---

#### FEATURE 7.4.5 — Template policy (`AUDIT_POLICY.md`)
**Labels:** `feature` `phase-2` `task-7-4`  
**File:** `contracts/AUDIT_POLICY.md`

**Technical description**  
Document with mandatory rules:
- No template may have `is_active=True` without an associated `audit_report_url`
- Audit report must be from a specialized external firm (e.g. Trail of Bits, OpenZeppelin, Certik)
- Template with changes to access control logic (`owner`, `minter`) requires a new audit
- Audit version and date must appear in `ContractTemplate`

**DoD**
- [ ] Document exists and linked from the DeFi context README
- [ ] Integration test verifies no `is_active=True` template has empty `audit_report_url`

---

## GitHub label reference

| Label | Description | Suggested color |
|-------|-------------|----------------|
| `epic` | Epic-level item | `#6e40c9` |
| `task` | Task-level item | `#0075ca` |
| `feature` | Feature-level item | `#28a745` |
| `phase-1` | Zero-license MVP | `#e4e669` |
| `phase-2` | Tokenization | `#f9a825` |
| `compliance` | Regulatory compliance related | `#d93f0b` |
| `blockchain` | Blockchain / web3.py interaction | `#1d76db` |
| `infra` | Workers, queues, indexer | `#bfd4f2` |
| `api` | FastAPI endpoints | `#84b6eb` |
| `blocked` | Waiting on dependency | `#b60205` |

## Suggested milestones

| Milestone | Included epics | Completion criterion |
|-----------|---------------|---------------------|
| **F1 – Zero-License MVP** | EPIC 1–6 | Quotes + Wallet + Research in production, Compliance active |
| **F2 – Tokenization** | EPIC 7 | Audited ERC-20/721/1155 templates + non-custodial deploy functional |
| **F3 – Robo-Advisor** | (future) | After regulatory registration decision |
