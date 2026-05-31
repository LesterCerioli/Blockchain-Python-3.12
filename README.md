# CryptoBank

> A crypto-native digital bank. Everything a traditional bank offers — accounts, transfers, payments, investments and financing — with cryptocurrency at its core, and seamless conversion between fiat (USD, EUR, BRL) and crypto. **BTC** and **ETH** at launch.

Built with **Python 3.12** and **FastAPI**.

---

## What CryptoBank is

CryptoBank lets customers:

- Open multi-currency accounts (fiat + crypto).
- Deposit and withdraw crypto to/from external blockchain addresses.
- **Convert** fiat ↔ crypto and crypto ↔ crypto at a quoted rate.
- Send instant internal transfers to other CryptoBank customers.
- Invest (staking / yield products).
- Finance assets via crypto-collateralized loans.
- Use everyday financial services (statements, fees, notifications).

The bank uses a **custodial model**: it securely holds private keys (via HSM/KMS), so customers get a familiar banking experience without managing keys themselves.

---

## Documentation index

| Document | Description |
|----------|-------------|
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | The full Solution Architecture Document: contexts, flows, data, security, compliance, infrastructure. |
| `README.md` (this file) | Project overview, implemented modules, conventions, and how to run locally. |
| `migrations/ethereum/001_create_eth_providers.sql` | PostgreSQL DDL for the `eth_providers` table (UUID v4 PK). |

Start with **`ARCHITECTURE.md`** for the complete design.

---

## Architecture at a glance

```mermaid
graph LR
    CUST[Customer] --> GW[API Gateway / BFF]
    GW --> CORE[Domain Microservices]
    CORE --> LEDGER[(Double-entry Ledger)]
    CORE --> EXCH[Conversion & Exchange Engine]
    EXCH --> CHAIN[Blockchain Integration]
    CHAIN --> CUSTODY[Custody / HSM]
    CHAIN --> BTC[(Bitcoin)]
    CHAIN --> ETH[(Ethereum)]
    CORE --> COMP[Compliance / KYC-AML]
```

Core ideas:

- **Ledger is the single source of truth** — immutable, double-entry, integer-only money.
- **Off-chain first, on-chain at the edge** — internal transfers are instant ledger postings; the blockchain is touched only for deposits/withdrawals.
- **Event-driven microservices** organized by DDD bounded contexts.
- **Compliance and security are first-class**, not add-ons.

---

## Technology stack

- **Runtime:** Python 3.12
- **API:** FastAPI (ASGI), Pydantic v2
- **Databases:** PostgreSQL (ledger/transactional), Redis (cache/locks)
- **Messaging:** Apache Kafka (domain events, sagas)
- **Blockchain:** Bitcoin & Ethereum nodes/providers behind a chain-abstraction layer
- **Custody:** HSM/KMS + dedicated Signing Service
- **Infra:** Docker, Kubernetes, Terraform, OpenTelemetry/Prometheus/Grafana

---

## Suggested repository layout

```
cryptobank/
├── services/
│   ├── identity/                 # AuthN/AuthZ, OAuth2/OIDC, MFA
│   ├── onboarding-kyc/           # registration + KYC/AML
│   ├── accounts-wallets/         # fiat accounts + custodial crypto wallets
│   ├── ledger/                   # double-entry accounting (source of truth)
│   ├── transactions/             # internal transfers, transaction lifecycle
│   ├── payments/                 # fiat rails (PIX/SEPA/SWIFT via PSP)
│   ├── exchange/                 # conversion & exchange engine
│   ├── market-data/              # pricing & spreads
│   ├── blockchain/               # chain adapters (BTC, ETH)
│   ├── custody/                  # signing service (talks to HSM)
│   ├── investments/              # staking / yield / portfolios
│   ├── lending/                  # crypto-collateralized loans
│   ├── compliance/               # monitoring, screening, travel rule
│   ├── notifications/            # email / SMS / push
│   └── audit/                    # immutable audit & reporting
├── libs/
│   ├── money/                    # integer-money types (cents, satoshis, wei)
│   ├── events/                   # event schemas + outbox helpers
│   └── common/                   # config, logging, tracing, errors
├── deploy/
│   ├── k8s/                      # manifests / Helm charts
│   └── terraform/                # infrastructure as code
└── docs/
    ├── ARCHITECTURE.md
    └── adr/                      # Architecture Decision Records
```

Each service follows **hexagonal architecture**: a domain core isolated from adapters (HTTP, DB, messaging, chain providers).

---

## Conventions

- **Money is an integer.** Always store amounts in the smallest unit (cents, satoshis, wei) with explicit `currency` + `scale`. Never use floats for money.
- **Idempotency-Key** header is mandatory on all state-changing financial endpoints.
- **Database-per-service.** No shared schemas across contexts.
- **Outbox pattern** for publishing domain events atomically with state changes.
- **Async-first** FastAPI endpoints (`async def`) for all I/O-bound work.
- **No secrets in code.** Use Vault; private keys never leave the HSM.

---

## Local development (illustrative)

> The commands below illustrate the intended developer experience for a single service. Adapt per service.

```bash
# Requirements: Python 3.12, Docker, docker compose

# 1. Bring up infra (Postgres, Redis, Kafka, local chain nodes/mocks)
docker compose up -d

# 2. Create and activate a virtual environment
python3.12 -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
alembic upgrade head

# 5. Start the service (example: exchange engine)
uvicorn services.exchange.main:app --reload --port 8080
```

Interactive API docs are then available at `http://localhost:8080/docs` (FastAPI / OpenAPI).

---

## Status

The solution architecture and core documentation are in place. Implementation is in progress following the phased roadmap described in `ARCHITECTURE.md` (§19). The modules below are already implemented and tested.

---

## Implemented

### Smart Contract Generator (`app/`)

FastAPI microservice that generates Solidity source code for ERC20 tokens on demand.

| Endpoint | Description |
|----------|-------------|
| `POST /generate/erc20/` | Generates ERC20 Solidity contract from token properties (name, symbol, supply, decimals) |
| `POST /service/prepare-contract-interaction/` | Prepares contract interaction data (ABI-ready placeholder) |

Key classes:

- `ERC20ContractGenerator` — produces Solidity source for standard ERC20 tokens (transfer, approve, transferFrom, events).
- `format_token_transfer_data` / `prepare_contract_interaction_data` — token service utilities.

---

### Ethereum Blockchain Service (`services/blockchain/ethereum/`)

Full production-grade service for Ethereum RPC integration, built with **hexagonal architecture** (ports & adapters / DIP). Entry point: `uvicorn services.blockchain.ethereum:app`.

#### Domain layer

| Module | Contents |
|--------|----------|
| `domain/entities/` | `ProviderRecord`, `ProviderStatus`, `ChainConfig`, `NetworkName`, `CHAIN_ID_TO_NETWORK`, `CHAIN_BLOCK_TIME` |
| `domain/interfaces/` | `IProviderRepository`, `IHealthMonitor`, `IChainAdapter`, `INetworkService` and their value objects (`ProviderHealth`, `BlockInfo`, `NetworkInfo`) |
| `domain/adapters/` | `EthChainAdapter` — translates `IChainAdapter` calls into `MultiProvider` calls (satisfies DIP) |

#### Application layer

| Service | Responsibility |
|---------|----------------|
| `HealthService` | Checks all providers in parallel, records state in the repository, detects stale blocks |
| `NetworkService` | Resolves chain ID → network name and sync status via `IChainAdapter` |

#### Infrastructure layer

| Sub-package | Contents |
|-------------|----------|
| `infrastructure/rpc/` | `EthRpcClient` — async JSON-RPC 2.0 client with connection pooling (httpx); `CircuitBreaker` — three-state (closed / open / half-open) circuit breaker |
| `infrastructure/providers/` | `BaseProvider` (abstract, owns circuit breaker), `RpcProvider` (concrete JSON-RPC transport), `MultiProvider` (priority-ordered failover), `ProviderFactory` (builds providers from config dicts) |
| `infrastructure/persistence/` | `Database` (async SQLAlchemy engine + session factory), `EthProviderModel` (ORM model), `PostgresProviderRepository` (production), `InMemoryProviderRepository` (tests / local dev) |
| `infrastructure/config/` | `EthereumSettings` — pydantic-settings class, reads from env vars with `ETH_` prefix or `.env` file |

#### API layer

| Module | Contents |
|--------|----------|
| `api/routers/` | `GET /v1/eth/health` — provider health + current block height; `GET /v1/eth/network` — chain ID, network name, sync status |
| `api/schemas/` | `HealthResponse`, `ProviderHealthSchema`, `NetworkResponse` (Pydantic v2) |
| `api/dependencies.py` | FastAPI dependency injectors that pull services from `app.state` |

#### Database migration

| File | Description |
|------|-------------|
| `migrations/ethereum/001_create_eth_providers.sql` | Creates `eth_providers` table with **UUID v4 primary key** (`gen_random_uuid()` — generated by the database, never by the application), status/priority indexes, and column comments |

> **SQL injection:** all queries go through SQLAlchemy ORM (`insert().values(...)`, `select().where(...)`), which uses parameterized statements automatically. No raw SQL strings in service code.

#### Running the Ethereum service

```bash
# Start with a PostgreSQL instance reachable at the default URL, then:
uvicorn services.blockchain.ethereum:app --reload --port 8001
```

Override defaults via environment variables (prefix `ETH_`):

```bash
ETH_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
ETH_STALE_BLOCK_THRESHOLD_SECONDS=30 \
uvicorn services.blockchain.ethereum:app --port 8001
```

#### Running the tests

```bash
pytest tests/blockchain/ -v
```

All 21 unit tests cover: circuit breaker state machine, multi-provider failover, health service (parallel checks, stale detection, DB-failure isolation), and API endpoints.

---

## A note on regulation

CryptoBank operates as a regulated financial entity. KYC/AML, sanctions screening, the travel rule and auditability are designed into the platform. Licensing and jurisdiction-specific obligations are handled at the corporate level and drive configuration of the compliance gates.