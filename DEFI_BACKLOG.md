# Backlog — DeFi Module (Non-Custodial SaaS)

> Derived from: `arquitetura-solucao-defi.html` v1.0 · May 31, 2026  
> Guiding principle: **zero financial license cost** — every item must respect the seven non-crossable boundaries defined in the architecture document.

---

## Phase legend

| Phase | Scope |
|-------|-------|
| **F1** | Zero-license MVP — Quotes, Non-custodial Wallet, Impersonal Research |
| **F2** | Generic tokenization tooling |
| **F3** | Regulated robo-advisor (out of current scope — only enters after registration decision) |

---

## EPIC 1 — DeFi Context Foundation

> Establishes the isolated *bounded context* inside the existing FastAPI monorepo, without leaking blockchain logic into existing code.

---

### TASK 1.1 — DDD Bounded Context Structure

**Goal:** create `services/defi/` with the same DDD layers already adopted in `services/blockchain/ethereum/`.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 1.1.1 | Create `services/defi/` package with subpackages `domain/`, `application/`, `infrastructure/`, `api/` | Directory structure and `__init__.py` in each layer |
| 1.1.2 | Define domain entities: `Quote`, `MarketIndex`, `WalletSession`, `UnsignedTransaction`, `ResearchReport` | Pydantic/dataclass classes in `domain/entities/` |
| 1.1.3 | Define *value objects*: `TokenAddress`, `ChainId`, `FiatPrice`, `CryptoAmount`, `TxHash` | Immutable types with validation in `domain/value_objects/` |
| 1.1.4 | Define domain interfaces (ports): `IMarketDataProvider`, `IWalletConnector`, `ITransactionBuilder`, `IResearchRepository` | ABCs in `domain/interfaces/` |
| 1.1.5 | DeFi exception hierarchy: `DeFiError`, `MarketDataError`, `WalletConnectionError`, `NonCustodialViolationError` | `domain/exceptions.py` |

---

### TASK 1.2 — API Contract and Routing

**Goal:** register DeFi routes in FastAPI with a versioned prefix and shared schemas, without altering existing routes.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 1.2.1 | Create DeFi router with prefix `/api/v1/defi` and include it in `app/main.py` via `include_router` | `services/defi/api/routers/__init__.py` + registration in `main.py` |
| 1.2.2 | Shared response schemas: `PaginatedResponse[T]`, `ErrorResponse`, `HealthResponse` | `services/defi/api/schemas/common.py` |
| 1.2.3 | FastAPI dependencies for the DeFi context: `get_defi_settings`, `get_market_provider`, `get_wallet_service` | `services/defi/api/dependencies.py` |
| 1.2.4 | OpenAPI tags and descriptions that make the non-custodial model explicit to API consumers | Tag metadata in `main.py` |

---

### TASK 1.3 — Configuration and Environment

**Goal:** isolate DeFi module configuration using Pydantic Settings, without mixing with existing Ethereum settings.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 1.3.1 | `DeFiSettings` (Pydantic BaseSettings) with market data variables, rate limits, cache TTL | `services/defi/infrastructure/config/settings.py` |
| 1.3.2 | Multi-chain configuration: map `chain_id → RPC URL` for Ethereum mainnet, Polygon, Arbitrum, Base | `DEFI_CHAINS` section in `DeFiSettings` |
| 1.3.3 | External API key management (market data) via environment variables; **never** store client keys | Updated `.env.example` + validation in settings |
| 1.3.4 | Configuration tests ensuring no field in `DeFiSettings` accepts a client private key | `tests/defi/test_settings.py` |

---

## EPIC 2 — Quotes & Indices (Phase 1)

> Read-only information product. Acquisition flagship and lowest regulatory risk. All data is impersonal — identical for all subscribers.

---

### TASK 2.1 — Market Data Provider Integration

**Goal:** implement adapters for external APIs with failover, mirroring the existing `multi_provider.py` pattern.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 2.1.1 | CoinGecko adapter (Free/Pro): spot prices, history, market cap | `infrastructure/market_data/coingecko_adapter.py` |
| 2.1.2 | CoinMarketCap adapter as alternative provider | `infrastructure/market_data/cmc_adapter.py` |
| 2.1.3 | `MultiMarketDataProvider`: automatic failover between providers using the existing circuit breaker | `infrastructure/market_data/multi_provider.py` |
| 2.1.4 | Per-provider rate limiting with exponential backoff | Integrated into `MultiMarketDataProvider` |
| 2.1.5 | Unit tests with mocked adapters and integration tests against each API sandbox | `tests/defi/market_data/` |

---

### TASK 2.2 — Quotes Service

**Goal:** expose prices and variations via API, with cache, without personalization.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 2.2.1 | `QuoteService` (application layer): resolves quote via `IMarketDataProvider`, applies cache | `application/quote_service.py` |
| 2.2.2 | `GET /defi/quotes/{symbol}` — spot quote with bid/ask, 24h change, volume | Router + schema `QuoteResponse` |
| 2.2.3 | `GET /defi/quotes?symbols=BTC,ETH,SOL` — batch quotes (max 50 assets per request) | Endpoint with limit validation |
| 2.2.4 | `GET /defi/quotes/{symbol}/history?interval=1h&from=&to=` — OHLCV history | Endpoint + schema `OHLCVResponse` |
| 2.2.5 | Redis cache with configurable TTL (default 30 s for spot, 5 min for history) | `infrastructure/cache/redis_quote_cache.py` |

---

### TASK 2.3 — Market Indices and Rankings

**Goal:** publish protocol/token rankings equally to all subscribers; no personalized curation.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 2.3.1 | `IndexService`: composes and serves indices (DeFi TVL, Top 100 by market cap) | `application/index_service.py` |
| 2.3.2 | `GET /defi/indices` — list of available indices with metadata | Endpoint + schema `IndexListResponse` |
| 2.3.3 | `GET /defi/indices/{index_id}` — index composition and performance | Endpoint + schema `IndexDetailResponse` |
| 2.3.4 | `GET /defi/rankings/tokens?metric=market_cap&chain=ethereum` — filterable rankings by metric and chain | Paginated endpoint |
| 2.3.5 | `GET /defi/rankings/protocols?metric=tvl` — DeFi protocol TVL and fees (via DeFiLlama or similar) | Endpoint + DeFiLlama adapter |

---

## EPIC 3 — Non-Custodial Wallet & Transactions (Phase 1)

> Core invariant: **the platform builds the unsigned transaction; the client signs; funds never pass through the company.**

---

### TASK 3.1 — Wallet Connection

**Goal:** manage client wallet sessions without ever receiving or storing private keys.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 3.1.1 | `WalletSessionService`: creates and revokes wallet sessions (stores only public address + chain) | `application/wallet_session_service.py` |
| 3.1.2 | `POST /defi/wallet/connect` — receives public address and chain, returns session token | Endpoint + schema `WalletConnectRequest/Response` |
| 3.1.3 | EVM address validation (EIP-55 checksum) and ENS resolution via `web3.py` | `domain/value_objects/token_address.py` |
| 3.1.4 | `DELETE /defi/wallet/disconnect` — revokes session; no key data was stored to delete | Endpoint |
| 3.1.5 | Architecture test (pytest) asserting no field in session schemas or entities accepts `private_key` | `tests/defi/test_non_custodial_boundary.py` |

---

### TASK 3.2 — Unsigned Transaction Builder

**Goal:** build EIP-1559 transactions ready for the client to sign — the server never signs.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 3.2.1 | `TransactionBuilderService`: assembles `UnsignedTransaction` objects with `to`, `data`, `value`, `nonce`, `maxFeePerGas`, `maxPriorityFeePerGas` | `application/transaction_builder_service.py` |
| 3.2.2 | `POST /defi/transactions/estimate` — returns unsigned transaction + gas estimate | Endpoint + schema `TxEstimateRequest/Response` |
| 3.2.3 | Builder for ERC-20 transfers (`transfer`, `approve`, `transferFrom`) | `domain/builders/erc20_tx_builder.py` |
| 3.2.4 | Builder for Uniswap V2/V3 swaps (assembles calldata, does not execute) | `domain/builders/uniswap_tx_builder.py` |
| 3.2.5 | Non-custody guard: middleware that rejects any request containing `private_key`, `seed_phrase` or `mnemonic` fields | `api/middleware/non_custodial_guard.py` |
| 3.2.6 | Tests verifying the service raises `NonCustodialViolationError` if server-side signing is attempted | `tests/defi/test_tx_builder.py` |

---

### TASK 3.3 — Transaction Broadcast and Monitoring

**Goal:** receive the already-signed transaction from the client and monitor on-chain confirmation.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 3.3.1 | `POST /defi/transactions/broadcast` — receives `signed_tx_hex` from client and propagates to the network via `web3.py` | Endpoint + schema `BroadcastRequest/Response` |
| 3.3.2 | `GET /defi/transactions/{tx_hash}/status` — returns `pending | confirmed | failed` + confirmation count | Endpoint + schema `TxStatusResponse` |
| 3.3.3 | Async worker (ARQ/Celery) for confirmation polling and client notification via webhook/SSE | `infrastructure/workers/tx_confirmation_worker.py` |
| 3.3.4 | Idempotency: `Idempotency-Key` header on broadcast; prevents double submission | Middleware + table `defi_broadcast_idempotency` |
| 3.3.5 | `GET /defi/transactions/history?wallet={address}` — indexed transaction history for the address | Paginated endpoint via indexer (see Epic 5) |

---

### TASK 3.4 — Portfolio View (Read-Only)

**Goal:** display client's on-chain positions via direct blockchain reads — no custody, read-only.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 3.4.1 | `GET /defi/portfolio/{wallet_address}/balances` — native ETH + relevant ERC-20 balances | Endpoint + `PortfolioService` |
| 3.4.2 | Batch ERC-20 balance reader (`eth_call` multicall via Multicall3) | `infrastructure/chain/multicall_reader.py` |
| 3.4.3 | `GET /defi/portfolio/{wallet_address}/nfts` — ERC-721/1155 holdings | Endpoint + Transfer event indexer |
| 3.4.4 | `GET /defi/portfolio/{wallet_address}/defi-positions` — Aave, Uniswap LP positions (read-only via subgraph) | Endpoint + subgraph adapters |

---

## EPIC 4 — Impersonal Research (Phase 1)

> All content is published equally to all subscribers — no personalization by profile or wallet. This boundary is what keeps the module outside the investment advisory regime.

---

### TASK 4.1 — Research Content Model

**Goal:** structure and publish market reports and analysis in an impersonal, versioned format.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 4.1.1 | `ResearchReport` entity: `id`, `title`, `body_markdown`, `published_at`, `categories[]`, `tags[]`, `version` | `domain/entities/research_report.py` |
| 4.1.2 | `IResearchRepository` and PostgreSQL implementation with FTS (`tsvector`) | Interface + `infrastructure/persistence/research_repository.py` |
| 4.1.3 | Alembic migration for table `defi_research_reports` with FTS index | `migrations/defi/` |
| 4.1.4 | Impersonality guard: validation that prevents `user_id` or `wallet_address` fields in the publication payload | `domain/research_publisher.py` |

---

### TASK 4.2 — Research API

**Goal:** public endpoints (for subscribers) for listing, detail and full-text search.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 4.2.1 | `GET /defi/research` — paginated list with filters by category, tag and date | Endpoint + `ResearchListResponse` |
| 4.2.2 | `GET /defi/research/{id}` — full report | Endpoint + `ResearchDetailResponse` |
| 4.2.3 | `GET /defi/research/search?q={term}` — impersonal full-text search | Endpoint using PostgreSQL `tsvector` |
| 4.2.4 | Published content cache with CDN-friendly headers (`Cache-Control`, `ETag`) | HTTP cache middleware |

---

### TASK 4.3 — Public Rankings

**Goal:** publish market rankings accessible equally to all subscribers.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 4.3.1 | `GET /defi/research/rankings/protocols` — top protocols by TVL, volume, fees | Endpoint + `ProtocolRankingResponse` |
| 4.3.2 | `GET /defi/research/rankings/chains` — L1/L2 comparison by throughput, TVL, gas cost | Endpoint + `ChainRankingResponse` |
| 4.3.3 | Periodic ranking update via worker (cron every 15 min) | Worker + ARQ/Celery scheduler |

---

## EPIC 5 — Off-Chain Infrastructure (Workers & Indexer)

> On-chain confirmations, idempotency and event indexing without custody.

---

### TASK 5.1 — Async Workers

**Goal:** configure task queue for the DeFi context, isolated from other module queues.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 5.1.1 | ARQ (or Celery with Redis) setup for DeFi workers; configuration in `services/defi/infrastructure/workers/` | `worker_settings.py` + `Procfile`/Docker entry |
| 5.1.2 | Task definitions: `confirm_transaction`, `update_prices`, `index_events`, `refresh_rankings` | `infrastructure/workers/tasks.py` |
| 5.1.3 | Idempotency layer: before executing task, checks deduplication key in Redis | `infrastructure/workers/idempotency.py` |
| 5.1.4 | Dead letter queue (DLQ) + retry policy with exponential backoff (3 attempts, max 5 min) | Worker configuration |
| 5.1.5 | Worker health check endpoint integrated into `GET /health` | `application/health_service.py` update |

---

### TASK 5.2 — On-Chain Indexer

**Goal:** read blockchain events without custody — read-only access to public state.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 5.2.1 | `BlockListener`: subscribes to new blocks via `web3.py` (websocket or polling) | `infrastructure/indexer/block_listener.py` |
| 5.2.2 | `Transfer` event indexer (ERC-20/721) for monitored addresses | `infrastructure/indexer/erc20_transfer_indexer.py` |
| 5.2.3 | Uniswap V2/V3 swap event indexer (`Swap`, `Mint`, `Burn`) | `infrastructure/indexer/uniswap_event_indexer.py` |
| 5.2.4 | Persistence schema: table `defi_indexed_events` (block, tx_hash, event, args, indexed_at) | Alembic migration |
| 5.2.5 | Indexer lag monitor: alert if `current_block - indexed_block > 10` | `application/indexer_health_service.py` |

---

### TASK 5.3 — Reconciliation and Data Integrity

**Goal:** ensure consistency between local state and blockchain, including reorgs.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 5.3.1 | Reconciliation worker: periodically compares local ERC-20 balances with `eth_call` on-chain | `infrastructure/workers/reconciliation_worker.py` |
| 5.3.2 | Reorg detector: when `block.parentHash` doesn't match, marks affected events as `orphaned` and re-indexes | `infrastructure/indexer/reorg_detector.py` |
| 5.3.3 | Lost block recovery: upon detecting a block gap, indexes retroactively | `infrastructure/indexer/gap_recovery.py` |

---

## EPIC 6 — Compliance and Non-Custodial Guards

> Zero financial license cost does not mean zero compliance cost. This epic implements the remaining obligations from the architecture document: OFAC screening, audit trail, ToU and the technical guards that make non-custody verifiable by code.

---

### TASK 6.1 — OFAC / Sanctions Screening

**Goal:** not serve, knowingly, sanctioned persons or jurisdictions.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 6.1.1 | Integration with sanctions screening API (Chainalysis, TRM Labs or public OFAC SDN list) | `infrastructure/compliance/sanctions_checker.py` |
| 6.1.2 | Screening middleware: every wallet address passed to the API is checked against the sanctions list before processing | `api/middleware/sanctions_guard.py` |
| 6.1.3 | Jurisdiction blocking: list of sanctioned countries/regions (OFAC country programs) | `domain/compliance/jurisdiction_blocklist.py` |
| 6.1.4 | Screening audit log: every result (pass/block) recorded with timestamp and hashed address | `infrastructure/compliance/audit_logger.py` |

---

### TASK 6.2 — Non-Custodial Technical Guards

**Goal:** prevent by code that any part of the system touches client private keys.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 6.2.1 | `NonCustodialGuard` middleware: rejects (HTTP 422) any payload with `private_key`, `seed_phrase`, `mnemonic`, `keystore` fields | `api/middleware/non_custodial_guard.py` |
| 6.2.2 | Signing guardrail: `TransactionBuilderService` raises `NonCustodialViolationError` if called with `sign=True` argument | Logic in `application/transaction_builder_service.py` |
| 6.2.3 | Architecture test (AST scan via `ast` stdlib): verifies no module in `services/defi/` imports `eth_account.Account.sign_transaction` directly | `tests/defi/test_arch_non_custodial.py` |
| 6.2.4 | Billing isolation test: verifies no code in the DeFi transaction flow calls billing functions | `tests/defi/test_arch_billing_isolation.py` |

---

### TASK 6.3 — Audit Trail

**Goal:** complete traceability of all DeFi platform actions for internal and future regulatory audit.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 6.3.1 | `AuditLogger`: records each DeFi API call with `user_id`, `wallet_address` (public), `endpoint`, `payload_hash`, `ip`, `timestamp` | `infrastructure/audit/audit_logger.py` |
| 6.3.2 | Immutable audit log storage: table `defi_audit_log` with `INSERT`-only (no UPDATE/DELETE via app) | Migration + PostgreSQL policy |
| 6.3.3 | Log retention: worker that archives logs older than 7 years to cold storage (S3/GCS) | `infrastructure/workers/log_archival_worker.py` |
| 6.3.4 | `GET /internal/defi/audit?wallet={addr}&from=&to=` — internal endpoint (authenticated by admin API key) to query audit trail | Restricted endpoint |

---

### TASK 6.4 — Terms of Use

**Goal:** make unambiguous that the client is the operator and responsible party — a requirement of the non-custodial SaaS model.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 6.4.1 | `ToUService`: verifies if the user has accepted the current ToU version before using DeFi features | `application/tou_service.py` |
| 6.4.2 | `ToUCheckMiddleware`: blocks DeFi routes (HTTP 403 with `tou_required`) if ToU not accepted | `api/middleware/tou_middleware.py` |
| 6.4.3 | `POST /defi/terms/accept` — records acceptance with `version`, `timestamp`, `ip`, `user_id` | Endpoint + table `defi_tou_acceptances` |
| 6.4.4 | ToU versioning: when a new major version is published, `requires_reaccept` flag forces new acceptance | `domain/entities/terms_of_use.py` |

---

## EPIC 7 — Generic Tokenization Tooling (Phase 2)

> The client is the issuer and the responsible party. The platform provides audited templates and builds unsigned transactions. **Requires prior legal validation** before enabling in production.

---

### TASK 7.1 — Smart Contract Template Library

**Goal:** provide audited, parameterizable templates via factory pattern; no freely generated contracts.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 7.1.1 | Audited ERC-20 template with parameters: `name`, `symbol`, `initial_supply`, `decimals`, `mintable`, `burnable` | `contracts/templates/ERC20Factory.sol` + Foundry tests |
| 7.1.2 | Audited ERC-721 (NFT) template with `name`, `symbol`, `base_uri`, `max_supply` | `contracts/templates/ERC721Factory.sol` + Foundry tests |
| 7.1.3 | Audited ERC-1155 (multi-token) template | `contracts/templates/ERC1155Factory.sol` + Foundry tests |
| 7.1.4 | Template versioning: each template has `version` and `audit_report_url`; platform only uses audited versions | `domain/entities/contract_template.py` |
| 7.1.5 | Template parameter validation in domain: rejects empty names, supply <= 0, etc. | `domain/validators/template_validator.py` |

---

### TASK 7.2 — Token Deployment Flow

**Goal:** build the unsigned deployment transaction and deliver it to the client to sign — the server is never `msg.sender`.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 7.2.1 | `TokenizationService`: selects template, encodes constructor, assembles `UnsignedTransaction` for deploy | `application/tokenization_service.py` |
| 7.2.2 | `POST /defi/tokenization/deploy/estimate` — receives token parameters, returns unsigned tx + gas estimate | Endpoint + `DeployEstimateRequest/Response` |
| 7.2.3 | Guard: `TokenizationService` verifies `deployer_address` came from the client and the server does not sign | Invariant in `application/tokenization_service.py` |
| 7.2.4 | `POST /defi/tokenization/deploy/confirm` — receives `tx_hash` of confirmed deploy, registers contract in local registry | Endpoint + table `defi_deployed_contracts` |
| 7.2.5 | `GET /defi/tokenization/contracts/{address}` — registered contract metadata (template used, deployer, chain, date) | Read-only endpoint |

---

### TASK 7.3 — Token Management Tools

**Goal:** provide transaction builders for post-deploy operations (mint, burn, transfer) — all unsigned.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 7.3.1 | `POST /defi/tokenization/{address}/mint/estimate` — assembles unsigned mint tx for client to sign | Endpoint + builder |
| 7.3.2 | `POST /defi/tokenization/{address}/burn/estimate` — assembles unsigned burn tx | Endpoint + builder |
| 7.3.3 | `POST /defi/tokenization/{address}/transfer/estimate` — assembles unsigned ERC-20 `transfer` tx | Endpoint + builder |
| 7.3.4 | `GET /defi/tokenization/{address}/metadata` — reads `name`, `symbol`, `totalSupply`, `owner` via `eth_call` (read-only) | Endpoint |

---

### TASK 7.4 — Contract Testing and Audit Pipeline

**Goal:** ensure only audited and tested contracts enter the template catalog.

#### Features

| # | Feature | Deliverable |
|---|---------|------------|
| 7.4.1 | Foundry suite for all templates: unit tests, fuzzing, invariant tests | `contracts/test/` |
| 7.4.2 | CI integration: `forge test` runs on every PR touching `contracts/` | `.github/workflows/contracts.yml` |
| 7.4.3 | Slither static analysis in CI: fails the build if High/Critical findings exist | CI step `slither .` |
| 7.4.4 | Gas report: `forge snapshot` generates committed `gas-snapshot`; gas regression diff on PRs | CI step + artifact |
| 7.4.5 | Template policy: documented rule prohibiting adding a new template without an associated external audit report | `contracts/AUDIT_POLICY.md` |

---

## Epic dependency map

```
EPIC 1 (Foundation)
  └── EPIC 2 (Quotes)             → depends on 1.1, 1.2, 1.3
  └── EPIC 3 (Wallet)             → depends on 1.1, 1.2, 1.3 + existing Ethereum connectivity
  └── EPIC 4 (Research)           → depends on 1.1, 1.2
  └── EPIC 5 (Off-chain Infra)    → depends on 1.3 + 3.3 (broadcast worker)
  └── EPIC 6 (Compliance)         → depends on 1.2 (middleware) + 3.1 (wallet sessions)
  └── EPIC 7 (Tokenization) [F2]  → depends on EPICs 1–6 complete + prior legal validation
```

---

## Boundaries that MUST NEVER be crossed (PR review checklist)

Before each feature PR, verify:

- [ ] Client private keys and funds **never** enter any endpoint, schema, log or database.
- [ ] No client value transits through company accounts or wallets — not even for an instant.
- [ ] Billing is always by subscription, charged separately; no DeFi feature retains or redirects transaction value.
- [ ] Recommendations and content are impersonal — published equally to all; no `user_id` field in research/ranking responses.
- [ ] Tokenization tooling is generic: the client is the `msg.sender` and the issuer; the platform does not structure specific use cases.
- [ ] The company never executes discretionary orders or signs transactions on behalf of the client.
- [ ] Smart contracts come exclusively from audited templates — free-form contract generation is prohibited.
