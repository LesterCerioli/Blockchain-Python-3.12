# DeFi SaaS Platform

> A non-custodial software platform for the DeFi ecosystem. Built as a pure technology product — subscriptions, not transactions — designed to operate with **zero financial license cost** at launch.

Built with **Python 3.12** and **FastAPI**.

---

## What this platform is

A SaaS product that gives users access to the DeFi ecosystem through tooling the company provides but never controls. The key distinction: the platform is **software**, not an intermediary.

- Market data and on-chain indices — information product, not financial advice.
- Non-custodial wallet connectivity — the client signs their own transactions; funds never touch the company's infrastructure.
- Impersonal research and rankings — published identically to all subscribers; no personalized recommendations.
- Generic tokenization tooling (phase 2) — audited smart contract templates; the client is the issuer and bears responsibility for classification.

The company **never holds client keys, never holds client funds, never routes value through its own accounts**. Revenue comes from subscription billing, kept entirely separate from any transaction flow.

---

## Architecture at a glance

```
┌─────────────────────────────────────────────────┐
│  Client layer                                   │
│  ┌─────────────────┐  ┌────────────────────┐   │
│  │  Web / mobile   │  │  Client wallet     │   │
│  │  (platform UI)  │  │  (keys stay here)  │   │
│  └─────────────────┘  └────────────────────┘   │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│  Monorepo FastAPI — non-custodial SaaS          │
│  ┌─────────────────┐  ┌────────────────────┐   │
│  │  Core platform  │  │  DeFi context      │   │
│  │  billing, auth  │  │  (bounded context) │   │
│  └─────────────────┘  └────────────────────┘   │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│  Off-chain infrastructure                       │
│  ┌─────────────────┐  ┌────────────────────┐   │
│  │  Workers/queues │  │  On-chain indexer  │   │
│  │  idempotency    │  │  read-only, no     │   │
│  └─────────────────┘  │  custody           │   │
│                        └────────────────────┘   │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│  External systems (outside company control)     │
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Market data │  │ Partners │  │Blockchain│  │
│  │  (read-only) │  │ on/off-  │  │  (EVM)   │  │
│  └──────────────┘  │ ramp     │  └──────────┘  │
│                     └──────────┘                │
└─────────────────────────────────────────────────┘
```

Core principles:

- **Non-custodial by design** — private keys and client funds never enter the platform or any company-controlled infrastructure.
- **Pure software, not an intermediary** — the platform provides the tool; the client operates it.
- **Billing outside the fund flow** — subscription revenue is collected separately; no value is retained from inside a transaction.
- **Impersonal content and neutral tooling** — research is published identically to all; tokenization templates are generic; the client decides the use.
- **DeFi context as an isolated bounded context** — DeFi modules live inside the FastAPI monorepo with an explicit boundary; no blockchain logic leaks into core services.

---

## DeFi modules (scope)

| Module | Phase | Status |
|--------|-------|--------|
| Market data & indices | 1 | Planned |
| Non-custodial wallet connectivity | 1 | Planned |
| Impersonal research & rankings | 1 | Planned |
| Billing (subscription) | 1 | Planned |
| Sanctions / OFAC screening | 1 | Planned |
| Generic tokenization tooling | 2 | Prototype — `app/` |

**Out of scope (initial):** personalized recommendations / robo-advisor. This feature triggers investment advisor registration (RIA in the US / Consultoria CVM in Brazil) regardless of being software. The bounded context boundary is already designed to receive this module in a future phase without rework.

---

## Technology stack

- **Runtime:** Python 3.12
- **API:** FastAPI (ASGI), Pydantic v2
- **Blockchain:** EVM / Ethereum via `web3.py` + wallet SDK (MetaMask); chain-abstraction layer already built
- **Async:** ARQ or Celery workers, idempotency and reconciliation
- **Indexing:** on-chain indexer (own subgraph or node service)
- **Databases:** PostgreSQL (async SQLAlchemy), Redis (cache / locks)
- **Operational keys:** KMS/HSM for company-owned deploy keys only — never client keys
- **Contracts (phase 2):** Solidity / Vyper · Foundry or Hardhat · audited templates
- **Infra:** Docker, Kubernetes, Terraform, OpenTelemetry / Prometheus / Grafana

---

## Repository layout

```
.
├── app/                          # Smart contract generator (ERC20) — implemented
│   ├── main.py
│   ├── contract_generator.py
│   └── token_services.py
├── services/
│   ├── blockchain/               # Chain abstraction layer — implemented
│   │   └── ethereum/             # EVM / Ethereum service (hexagonal arch.)
│   │       ├── api/
│   │       ├── application/
│   │       ├── domain/
│   │       └── infrastructure/
│   ├── market-data/              # Cotações & índices (phase 1)
│   ├── wallet/                   # Non-custodial wallet connectivity (phase 1)
│   ├── research/                 # Impersonal research & rankings (phase 1)
│   ├── billing/                  # Subscription billing (phase 1)
│   ├── compliance/               # Sanctions / OFAC screening (phase 1)
│   └── tokenization/             # Generic tokenization context (phase 2)
├── libs/
│   ├── events/                   # Event schemas + outbox helpers
│   └── common/                   # Config, logging, tracing, errors
├── migrations/
│   └── ethereum/
│       └── 001_create_eth_providers.sql
├── tests/
│   └── blockchain/
├── deploy/
│   ├── k8s/
│   └── terraform/
└── docs/
    ├── ARCHITECTURE.md
    └── adr/
```

Each service follows **hexagonal architecture**: a domain core isolated from HTTP, DB, messaging, and chain-provider adapters.

---

## Conventions

- **Non-custodial invariant.** No endpoint, worker, or migration may store, receive, or route client private keys or client funds.
- **Billing is always by subscription.** No fee may be deducted from inside a transaction flow.
- **Impersonal content.** Research and ranking output must be identical for all subscribers; no profile-based filtering.
- **Audited contracts only.** The tokenization module deploys from audited, versioned templates. No free-form contract generation that bypasses audit.
- **Idempotency-Key** header is mandatory on all state-changing endpoints.
- **Database-per-service.** No shared schemas across bounded contexts.
- **Outbox pattern** for publishing domain events atomically with state changes.
- **Async-first** FastAPI endpoints (`async def`) for all I/O-bound work.
- **No secrets in code.** Use Vault or KMS; company operational keys never appear in source.

---

## Local development

```bash
# Requirements: Python 3.12, Docker, docker compose

# 1. Bring up infrastructure (Postgres, Redis, local chain node or mock)
docker compose up -d

# 2. Create and activate a virtual environment
python3.12 -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
alembic upgrade head

# 5. Start a service (example: Ethereum blockchain service)
uvicorn services.blockchain.ethereum:app --reload --port 8001

# 6. Start the smart contract generator
uvicorn app.main:app --reload --port 8000
```

Interactive API docs: `http://localhost:<port>/docs`

---

## Status

Architecture and core infrastructure are in place. Phase 1 feature services are planned. The modules below are implemented and tested.

---

## Implemented

### Smart Contract Generator (`app/`)

FastAPI microservice that generates Solidity source code for ERC20 tokens on demand. Serves as the working prototype for the phase 2 generic tokenization context.

| Endpoint | Description |
|----------|-------------|
| `POST /generate/erc20/` | Generates ERC20 Solidity contract from token properties (name, symbol, supply, decimals) |
| `POST /service/prepare-contract-interaction/` | Prepares contract interaction data (ABI-ready placeholder) |

Key classes:

- `ERC20ContractGenerator` — produces Solidity source for standard ERC20 tokens (transfer, approve, transferFrom, events).
- `format_token_transfer_data` / `prepare_contract_interaction_data` — token service utilities.

---

### Ethereum Blockchain Service (`services/blockchain/ethereum/`)

Production-grade service for Ethereum RPC integration, built with **hexagonal architecture** (ports & adapters / DIP). This is the chain abstraction layer the DeFi context relies on. Entry point: `uvicorn services.blockchain.ethereum:app`.

#### Domain layer

| Module | Contents |
|--------|----------|
| `domain/entities/` | `ProviderRecord`, `ProviderStatus`, `ChainConfig`, `NetworkName`, `CHAIN_ID_TO_NETWORK`, `CHAIN_BLOCK_TIME` |
| `domain/interfaces/` | `IProviderRepository`, `IHealthMonitor`, `IChainAdapter`, `INetworkService` and value objects (`ProviderHealth`, `BlockInfo`, `NetworkInfo`) |
| `domain/adapters/` | `EthChainAdapter` — translates `IChainAdapter` calls into `MultiProvider` calls (satisfies DIP) |

#### Application layer

| Service | Responsibility |
|---------|----------------|
| `HealthService` | Checks all providers in parallel, records state in the repository, detects stale blocks |
| `NetworkService` | Resolves chain ID → network name and sync status via `IChainAdapter` |

#### Infrastructure layer

| Sub-package | Contents |
|-------------|----------|
| `infrastructure/rpc/` | `EthRpcClient` — async JSON-RPC 2.0 client with connection pooling (httpx); `CircuitBreaker` — three-state (closed / open / half-open) |
| `infrastructure/providers/` | `BaseProvider` (abstract, owns circuit breaker), `RpcProvider` (concrete JSON-RPC transport), `MultiProvider` (priority-ordered failover), `ProviderFactory` |
| `infrastructure/persistence/` | `Database` (async SQLAlchemy engine + session factory), `EthProviderModel` (ORM model), `PostgresProviderRepository` (production), `InMemoryProviderRepository` (tests) |
| `infrastructure/config/` | `EthereumSettings` — pydantic-settings, reads from env vars with `ETH_` prefix or `.env` |

#### API layer

| Module | Contents |
|--------|----------|
| `api/routers/` | `GET /v1/eth/health` — provider health + block height; `GET /v1/eth/network` — chain ID, network name, sync status |
| `api/schemas/` | `HealthResponse`, `ProviderHealthSchema`, `NetworkResponse` (Pydantic v2) |
| `api/dependencies.py` | FastAPI dependency injectors pulling services from `app.state` |

#### Database migration

| File | Description |
|------|-------------|
| `migrations/ethereum/001_create_eth_providers.sql` | Creates `eth_providers` table with UUID v4 primary key (`gen_random_uuid()` — DB-generated, never application-generated), status/priority indexes |

> All queries use SQLAlchemy ORM parameterized statements. No raw SQL strings in service code.

#### Running the Ethereum service

```bash
uvicorn services.blockchain.ethereum:app --reload --port 8001
```

Override defaults via environment variables (`ETH_` prefix):

```bash
ETH_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
ETH_STALE_BLOCK_THRESHOLD_SECONDS=30 \
uvicorn services.blockchain.ethereum:app --port 8001
```

#### Ethereum node provider — localhost vs. production

Locally, the service defaults to `http://localhost:8545` (see `infrastructure/config/settings.py`), which expects a local Ethereum node such as Hardhat or Anvil:

```bash
npx hardhat node   # or: anvil
```

**This will not work when deployed to Render (or any container host).** There is no Ethereum node inside the container, and `localhost:8545` resolves to nothing. The correct production approach is to use an external **RPC-as-a-Service** provider — they run the node for you:

| Provider | Free tier | Networks |
|----------|-----------|----------|
| [Infura](https://infura.io) | Yes | Mainnet, Sepolia, others |
| [Alchemy](https://alchemy.com) | Yes | Mainnet, Polygon, others |
| [QuickNode](https://quicknode.com) | Yes (limited) | Many |

Create an account, copy the endpoint URL, and set it as an environment variable in the Render dashboard — no code change required, since `EthereumSettings` already reads from the `ETH_` prefix:

```bash
# Example for Render environment variables
ETH_PROVIDERS=[{"name":"primary","url":"https://mainnet.infura.io/v3/YOUR_KEY","priority":1,"request_timeout":10.0,"circuit_breaker_failure_threshold":5,"circuit_breaker_recovery_seconds":60}]
```

A second Render instance running a full Ethereum node is not recommended — it is expensive and unnecessary when free RPC tiers are available.

#### Running the tests

```bash
pytest tests/blockchain/ -v
```

21 unit tests covering: circuit breaker state machine, multi-provider failover, health service (parallel checks, stale detection, DB-failure isolation), and API endpoints.

---

### DeFi Bounded Context — Foundation (`app/services/defi/`)

**Epic 1 / Task 1.1 — [issues #9, #16]**

Establishes the isolated `services/defi/` bounded context inside the FastAPI monorepo following the same DDD layering already adopted in `services/blockchain/ethereum/`. No DeFi logic leaks outside this context.

#### Package structure

```
app/services/defi/
├── domain/
│   ├── entities/          # Pydantic v2 domain entities (see below)
│   ├── value_objects/     # Frozen dataclasses (see FEATURE 1.1.3 below)
│   ├── interfaces/        # ABCs — no concrete implementation in the domain
│   └── exceptions.py      # DeFiError hierarchy
├── application/
│   └── quote_service.py   # QuoteService — orchestrates without infra dependencies
├── infrastructure/
│   ├── config/settings.py # DeFiSettings (DEFI_ prefix, separate from EthereumSettings)
│   ├── cache/
│   ├── market_data/
│   ├── persistence/
│   ├── workers/
│   ├── indexer/
│   ├── compliance/
│   └── audit/
└── api/
    ├── routers/           # FastAPI router — /v1/defi/quote
    ├── schemas/           # Pydantic v2 request/response schemas
    └── middleware/
```

#### Domain entities (`domain/entities/`)

| Class | Description |
|-------|-------------|
| `Token` | ERC20 token descriptor with address and chain validation |
| `Pool` | Liquidity pool with pair addresses, fee tier, and TVL |
| `Position` | LP or lending position tied to a wallet and pool |
| `Protocol` | DeFi protocol descriptor (name, version, chain) |
| `Quote` | Swap quote result (amount in/out, slippage, price impact) |
| `WalletSession` | Non-custodial session reference — holds address only, never private key |
| `UnsignedTransaction` | EVM transaction payload ready for client-side signing; signing fields (v/r/s) are rejected on construction |
| `MarketIndex` | On-chain index snapshot (symbol, value, timestamp) |
| `ResearchReport` | Impersonal research record (title, summary, price target) |

All entities use Pydantic v2 validation. `WalletSession` and `UnsignedTransaction` enforce the non-custodial invariant at the model level.

#### Domain interfaces (`domain/interfaces/`)

| Interface | Description |
|-----------|-------------|
| `ITokenRepository` | Port for token lookup by address and chain |
| `IPoolRepository` | Port for pool discovery and TVL queries |
| `IPositionRepository` | Port for user position reads and writes |
| `IPriceOracle` | Port for spot and historical price feeds |
| `ISwapService` | Port for quote computation and swap execution |

All interfaces are abstract base classes (`ABC`) with no concrete implementation in the domain layer.

#### Domain exceptions (`domain/exceptions.py`)

All exceptions inherit from `DeFiError` (the bounded-context base):

`TokenNotFoundError`, `PoolNotFoundError`, `NoPoolsForPairError`, `InsufficientLiquidityError`, `SlippageExceededError`, `ProtocolNotSupportedError`, `PriceUnavailableError`, `PositionNotFoundError`.

---

### DeFi Value Objects — FEATURE 1.1.3 (`app/services/defi/domain/value_objects/`)

**[issue #42]** — Five new immutable value objects added to the DeFi domain layer. All are `@dataclass(frozen=True)`: mutation raises `FrozenInstanceError` at runtime. Plug-and-play addition — existing value objects (`Address`, `Price`, `Slippage`, `TokenAmount`) are untouched.

| Class | File | Validation |
|-------|------|------------|
| `TokenAddress` | `token_address.py` | EIP-55 checksum via `web3.Web3.to_checksum_address()`; requires `0x` prefix; normalises to checksummed form regardless of input case |
| `ChainId` | `chain_id.py` | Validated against the supported set `{1, 137, 42161, 8453}`; any other value raises `ValueError` with the list of supported chains |
| `FiatPrice` | `fiat_price.py` | `amount >= 0`; `currency` must be a 3-letter alphabetic ISO 4217 code (normalised to uppercase) |
| `CryptoAmount` | `crypto_amount.py` | `raw >= 0`; `decimals ∈ [0, 18]`; exposes `as_decimal` property (`Decimal(raw) / 10**decimals`) |
| `TxHash` | `tx_hash.py` | Must match `^0x[0-9a-fA-F]{64}$`; stored lowercased |

**Supported chains for `ChainId`:**

| Chain ID | Network |
|----------|---------|
| 1 | Ethereum Mainnet |
| 137 | Polygon |
| 42161 | Arbitrum One |
| 8453 | Base |

**Usage example:**

```python
from app.services.defi.domain.value_objects import (
    TokenAddress, ChainId, FiatPrice, CryptoAmount, TxHash
)
from decimal import Decimal

# TokenAddress — normalises to EIP-55 checksum
addr = TokenAddress("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
# addr.value == "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

# ChainId — rejects unsupported networks
chain = ChainId(137)   # Polygon — OK
# ChainId(56)          # raises ValueError: Unsupported chain_id 56

# FiatPrice — ISO 4217 currency
price = FiatPrice(amount=Decimal("3500.00"), currency="usd")
# price.currency == "USD"

# CryptoAmount — smallest-unit representation
one_eth = CryptoAmount(raw=10**18, decimals=18)
# one_eth.as_decimal == Decimal("1")

# TxHash — 32-byte transaction identifier
tx = TxHash("0x" + "ab" * 32)
# tx.value is lowercased

# Immutability guaranteed
from dataclasses import FrozenInstanceError
try:
    addr.value = "0x..."   # raises FrozenInstanceError
except FrozenInstanceError:
    pass
```

#### Running the value objects tests

```bash
pytest tests/defi/domain/test_value_objects.py -v
```

70 unit tests covering: valid construction, EIP-55 normalisation, chain ID rejection, currency normalisation, `FrozenInstanceError` on mutation, and all invalid-input edge cases.

---

### DeFi Settings — FEATURE 1.3.1 (`app/services/defi/infrastructure/config/settings.py`)

**[issue #49]** — `DeFiSettings` extended with all platform-level configuration fields required to operate the DeFi bounded context. All fields have safe defaults — the service starts and serves requests without any environment variable defined.

`DeFiSettings` uses `pydantic-settings` with `env_prefix="DEFI_"`. Every field maps to a `DEFI_<FIELD_NAME>` environment variable.

#### Configuration reference

| Field | Env variable | Default | Type |
|-------|-------------|---------|------|
| `redis_url` | `DEFI_REDIS_URL` | `redis://localhost:6379/0` | `str` |
| `quote_cache_ttl_seconds` | `DEFI_QUOTE_CACHE_TTL_SECONDS` | `30` | `int` |
| `history_cache_ttl_seconds` | `DEFI_HISTORY_CACHE_TTL_SECONDS` | `300` | `int` |
| `market_data_timeout_seconds` | `DEFI_MARKET_DATA_TIMEOUT_SECONDS` | `10` | `int` |
| `max_symbols_per_batch` | `DEFI_MAX_SYMBOLS_PER_BATCH` | `100` | `int` |
| `coingecko_api_key` | `DEFI_COINGECKO_API_KEY` | `None` | `SecretStr` |
| `cmc_api_key` | `DEFI_CMC_API_KEY` | `None` | `SecretStr` |
| `ofac_api_key` | `DEFI_OFAC_API_KEY` | `None` | `SecretStr` |

#### API key security model

- API keys (`coingecko_api_key`, `cmc_api_key`, `ofac_api_key`) are declared as `Optional[SecretStr]`.
- Pydantic masks their values as `SecretStr('**********')` in any `repr()`, `str()`, or log output — no custom code required.
- Keys belong to the **platform operator**, not to end users. A single set of keys serves the entire subscriber base transparently.
- Keys are optional: the service starts without them (free-tier or mock fallback). Set them only in production via a secrets manager or CI/CD secret injection — never in source-controlled files.

#### Setting non-secret configuration in production

```bash
DEFI_REDIS_URL=redis://your-redis-host:6379/0
DEFI_QUOTE_CACHE_TTL_SECONDS=30
DEFI_HISTORY_CACHE_TTL_SECONDS=300
DEFI_MARKET_DATA_TIMEOUT_SECONDS=10
DEFI_MAX_SYMBOLS_PER_BATCH=100
```

Secret keys must be injected at deploy time via environment secrets — never committed to `.env` files in source control. See `.env.example` for the variable names.

---

## Regulatory boundaries

Zero financial license cost is not zero compliance. As a technology company the platform maintains:

- **Sanctions / OFAC screening** — the platform does not knowingly serve sanctioned persons or jurisdictions.
- **Terms of Service** — clearly establishing the client as operator and responsible party.
- **Data protection** obligations applicable to any software product.
- **Audited contract templates** — immutable versioning, full audit trail of which template version was deployed, by whom, and when.

What the platform deliberately does **not** do: hold client funds, hold client keys, route value through company accounts, execute discretionary orders, or provide personalized investment recommendations.

---

---

# Plataforma SaaS DeFi

> Uma plataforma de software não-custodial para o ecossistema DeFi. Construída como produto de tecnologia puro — assinaturas, não transações — projetada para operar com **custo de licença financeira zero** no lançamento.

Construída com **Python 3.12** e **FastAPI**.

---

## O que é esta plataforma

Um produto SaaS que dá aos usuários acesso ao ecossistema DeFi por meio de ferramentas que a empresa fornece, mas nunca controla. A distinção central: a plataforma é **software**, não intermediária.

- Dados de mercado e índices on-chain — produto de informação, não aconselhamento financeiro.
- Conectividade de carteira não-custodial — o cliente assina as próprias transações; fundos nunca tocam a infraestrutura da empresa.
- Pesquisa impessoal e rankings — publicados de forma idêntica para todos os assinantes; sem recomendações personalizadas.
- Ferramental de tokenização genérico (fase 2) — templates de smart contract auditados; o cliente é o emissor e o responsável pela classificação.

A empresa **nunca detém chaves dos clientes, nunca detém fundos dos clientes, nunca roteia valor por suas próprias contas**. A receita vem de assinatura, mantida inteiramente separada de qualquer fluxo de transação.

---

## Arquitetura em visão geral

```
┌─────────────────────────────────────────────────┐
│  Camada do cliente                              │
│  ┌─────────────────┐  ┌────────────────────┐   │
│  │  Web / mobile   │  │  Carteira do       │   │
│  │  (interface)    │  │  cliente           │   │
│  └─────────────────┘  │  (chaves ficam aqui│   │
│                        └────────────────────┘   │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│  Monorepo FastAPI — SaaS não-custodial          │
│  ┌─────────────────┐  ┌────────────────────┐   │
│  │  Plataforma     │  │  Contexto DeFi     │   │
│  │  billing, auth  │  │  (bounded context) │   │
│  └─────────────────┘  └────────────────────┘   │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│  Infraestrutura off-chain                       │
│  ┌─────────────────┐  ┌────────────────────┐   │
│  │  Workers/filas  │  │  Indexador on-chain│   │
│  │  idempotência   │  │  read-only, sem    │   │
│  └─────────────────┘  │  custódia          │   │
│                        └────────────────────┘   │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│  Sistemas externos (fora do controle da empresa)│
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Dados de    │  │Parceiros │  │Blockchain│  │
│  │  mercado     │  │on/off-   │  │  (EVM)   │  │
│  │  (read-only) │  │ramp      │  └──────────┘  │
│  └──────────────┘  └──────────┘                │
└─────────────────────────────────────────────────┘
```

Princípios centrais:

- **Não-custodial por desenho** — chaves privadas e fundos dos clientes nunca entram na plataforma nem em nenhuma infraestrutura controlada pela empresa.
- **Software puro, não intermediário** — a plataforma fornece a ferramenta; o cliente opera.
- **Billing fora do fluxo de fundos** — a receita de assinatura é cobrada separadamente; nenhum valor é retido de dentro de uma transação.
- **Conteúdo impessoal e ferramental neutro** — pesquisa publicada igualmente para todos; templates de tokenização são genéricos; o cliente decide o uso.
- **Contexto DeFi como bounded context isolado** — os módulos DeFi vivem dentro do monorepo FastAPI com fronteira explícita; lógica de blockchain não vaza para serviços centrais.

---

## Módulos DeFi (escopo)

| Módulo | Fase | Status |
|--------|------|--------|
| Dados de mercado e índices | 1 | Planejado |
| Conectividade de carteira não-custodial | 1 | Planejado |
| Pesquisa impessoal e rankings | 1 | Planejado |
| Billing (assinatura) | 1 | Planejado |
| Triagem de sanções / OFAC | 1 | Planejado |
| Ferramental de tokenização genérico | 2 | Protótipo — `app/` |

**Fora do escopo (fase inicial):** recomendações personalizadas / robo-advisor. Esta feature aciona registro como consultor de investimento (RIA nos EUA / Consultoria CVM no Brasil) independentemente de ser software. A fronteira do bounded context já está desenhada para receber este módulo em uma fase futura sem retrabalho.

---

## Stack tecnológica

- **Runtime:** Python 3.12
- **API:** FastAPI (ASGI), Pydantic v2
- **Blockchain:** EVM / Ethereum via `web3.py` + wallet SDK (MetaMask); camada de abstração de chain já construída
- **Assíncrono:** workers ARQ ou Celery, idempotência e reconciliação
- **Indexação:** indexador on-chain (subgraph próprio ou serviço de nó)
- **Bancos de dados:** PostgreSQL (SQLAlchemy async), Redis (cache / locks)
- **Chaves operacionais:** KMS/HSM apenas para chaves de deploy da empresa — nunca chaves de clientes
- **Contratos (fase 2):** Solidity / Vyper · Foundry ou Hardhat · templates auditados
- **Infra:** Docker, Kubernetes, Terraform, OpenTelemetry / Prometheus / Grafana

---

## Estrutura do repositório

```
.
├── app/                          # Gerador de smart contracts (ERC20) — implementado
│   ├── main.py
│   ├── contract_generator.py
│   └── token_services.py
├── services/
│   ├── blockchain/               # Camada de abstração de chain — implementado
│   │   └── ethereum/             # Serviço EVM / Ethereum (arquitetura hexagonal)
│   │       ├── api/
│   │       ├── application/
│   │       ├── domain/
│   │       └── infrastructure/
│   ├── market-data/              # Cotações & índices (fase 1)
│   ├── wallet/                   # Conectividade de carteira não-custodial (fase 1)
│   ├── research/                 # Pesquisa impessoal & rankings (fase 1)
│   ├── billing/                  # Billing por assinatura (fase 1)
│   ├── compliance/               # Triagem de sanções / OFAC (fase 1)
│   └── tokenization/             # Contexto de tokenização genérica (fase 2)
├── libs/
│   ├── events/                   # Schemas de eventos + helpers de outbox
│   └── common/                   # Config, logging, tracing, erros
├── migrations/
│   └── ethereum/
│       └── 001_create_eth_providers.sql
├── tests/
│   └── blockchain/
├── deploy/
│   ├── k8s/
│   └── terraform/
└── docs/
    ├── ARCHITECTURE.md
    └── adr/
```

Cada serviço segue **arquitetura hexagonal**: núcleo de domínio isolado de adaptadores HTTP, DB, mensageria e provedores de chain.

---

## Convenções

- **Invariante não-custodial.** Nenhum endpoint, worker ou migration pode armazenar, receber ou rotear chaves privadas ou fundos de clientes.
- **Billing sempre por assinatura.** Nenhuma taxa pode ser deduzida de dentro de um fluxo de transação.
- **Conteúdo impessoal.** Saídas de pesquisa e rankings devem ser idênticas para todos os assinantes; sem filtragem baseada em perfil.
- **Somente contratos auditados.** O módulo de tokenização faz deploy a partir de templates auditados e versionados. Sem geração livre de contratos que bypass auditoria.
- **Idempotency-Key** obrigatório em todos os endpoints que alteram estado.
- **Database por serviço.** Sem schemas compartilhados entre bounded contexts.
- **Outbox pattern** para publicar eventos de domínio atomicamente com mudanças de estado.
- **Async-first** em endpoints FastAPI (`async def`) para todo trabalho I/O-bound.
- **Sem segredos no código.** Usar Vault ou KMS; chaves operacionais da empresa nunca aparecem no fonte.

---

## Desenvolvimento local

```bash
# Requisitos: Python 3.12, Docker, docker compose

# 1. Subir infraestrutura (Postgres, Redis, nó de chain local ou mock)
docker compose up -d

# 2. Criar e ativar ambiente virtual
python3.12 -m venv .venv && source .venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar migrações de banco de dados
alembic upgrade head

# 5. Iniciar um serviço (exemplo: serviço Ethereum blockchain)
uvicorn services.blockchain.ethereum:app --reload --port 8001

# 6. Iniciar o gerador de smart contracts
uvicorn app.main:app --reload --port 8000
```

Docs interativos da API: `http://localhost:<porta>/docs`

---

## Status

Arquitetura e infraestrutura central em vigor. Serviços de features da fase 1 planejados. Os módulos abaixo estão implementados e testados.

---

## Implementado

### Gerador de Smart Contracts (`app/`)

Microsserviço FastAPI que gera código-fonte Solidity para tokens ERC20 sob demanda. Serve como protótipo funcional para o contexto de tokenização genérica da fase 2.

| Endpoint | Descrição |
|----------|-----------|
| `POST /generate/erc20/` | Gera contrato Solidity ERC20 a partir de propriedades do token (nome, símbolo, supply, decimais) |
| `POST /service/prepare-contract-interaction/` | Prepara dados de interação com contrato (placeholder ABI-ready) |

Classes principais:

- `ERC20ContractGenerator` — produz código Solidity para tokens ERC20 padrão (transfer, approve, transferFrom, eventos).
- `format_token_transfer_data` / `prepare_contract_interaction_data` — utilitários de serviço de token.

---

### Serviço Blockchain Ethereum (`services/blockchain/ethereum/`)

Serviço de produção para integração com RPC Ethereum, construído com **arquitetura hexagonal** (ports & adapters / DIP). Esta é a camada de abstração de chain da qual o contexto DeFi depende. Entry point: `uvicorn services.blockchain.ethereum:app`.

#### Camada de domínio

| Módulo | Conteúdo |
|--------|----------|
| `domain/entities/` | `ProviderRecord`, `ProviderStatus`, `ChainConfig`, `NetworkName`, `CHAIN_ID_TO_NETWORK`, `CHAIN_BLOCK_TIME` |
| `domain/interfaces/` | `IProviderRepository`, `IHealthMonitor`, `IChainAdapter`, `INetworkService` e value objects (`ProviderHealth`, `BlockInfo`, `NetworkInfo`) |
| `domain/adapters/` | `EthChainAdapter` — traduz chamadas de `IChainAdapter` para `MultiProvider` (satisfaz DIP) |

#### Camada de aplicação

| Serviço | Responsabilidade |
|---------|-----------------|
| `HealthService` | Verifica todos os provedores em paralelo, registra estado no repositório, detecta blocos stale |
| `NetworkService` | Resolve chain ID → nome de rede e status de sincronização via `IChainAdapter` |

#### Camada de infraestrutura

| Sub-pacote | Conteúdo |
|------------|----------|
| `infrastructure/rpc/` | `EthRpcClient` — cliente JSON-RPC 2.0 assíncrono com connection pooling (httpx); `CircuitBreaker` — três estados (closed / open / half-open) |
| `infrastructure/providers/` | `BaseProvider` (abstrato, dono do circuit breaker), `RpcProvider` (transporte JSON-RPC concreto), `MultiProvider` (failover por prioridade), `ProviderFactory` |
| `infrastructure/persistence/` | `Database` (engine async SQLAlchemy + session factory), `EthProviderModel` (modelo ORM), `PostgresProviderRepository` (produção), `InMemoryProviderRepository` (testes) |
| `infrastructure/config/` | `EthereumSettings` — pydantic-settings, lê de variáveis de ambiente com prefixo `ETH_` ou arquivo `.env` |

#### Camada de API

| Módulo | Conteúdo |
|--------|----------|
| `api/routers/` | `GET /v1/eth/health` — saúde dos provedores + altura de bloco; `GET /v1/eth/network` — chain ID, nome de rede, status de sincronização |
| `api/schemas/` | `HealthResponse`, `ProviderHealthSchema`, `NetworkResponse` (Pydantic v2) |
| `api/dependencies.py` | Injetores de dependência FastAPI que buscam serviços de `app.state` |

#### Migração de banco de dados

| Arquivo | Descrição |
|---------|-----------|
| `migrations/ethereum/001_create_eth_providers.sql` | Cria tabela `eth_providers` com chave primária UUID v4 (`gen_random_uuid()` — gerado pelo banco, nunca pela aplicação), índices de status/prioridade |

> Todas as queries usam statements parametrizados do SQLAlchemy ORM. Sem strings SQL brutas no código de serviço.

#### Executando o serviço Ethereum

```bash
uvicorn services.blockchain.ethereum:app --reload --port 8001
```

Sobrescrever defaults via variáveis de ambiente (prefixo `ETH_`):

```bash
ETH_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
ETH_STALE_BLOCK_THRESHOLD_SECONDS=30 \
uvicorn services.blockchain.ethereum:app --port 8001
```

#### Executando os testes

```bash
pytest tests/blockchain/ -v
```

21 testes unitários cobrindo: máquina de estados do circuit breaker, failover multi-provider, health service (verificações em paralelo, detecção de stale, isolamento de falha de DB) e endpoints de API.

---

### Configurações DeFi — FEATURE 1.3.1 (`app/services/defi/infrastructure/config/settings.py`)

**[issue #49]** — `DeFiSettings` expandida com todos os campos de configuração de plataforma necessários para operar o contexto DeFi. Todos os campos têm defaults seguros — o serviço sobe e atende requisições sem nenhuma variável de ambiente definida.

`DeFiSettings` usa `pydantic-settings` com `env_prefix="DEFI_"`. Cada campo corresponde a uma variável de ambiente `DEFI_<NOME_DO_CAMPO>`.

#### Referência de configuração

| Campo | Variável de ambiente | Default | Tipo |
|-------|---------------------|---------|------|
| `redis_url` | `DEFI_REDIS_URL` | `redis://localhost:6379/0` | `str` |
| `quote_cache_ttl_seconds` | `DEFI_QUOTE_CACHE_TTL_SECONDS` | `30` | `int` |
| `history_cache_ttl_seconds` | `DEFI_HISTORY_CACHE_TTL_SECONDS` | `300` | `int` |
| `market_data_timeout_seconds` | `DEFI_MARKET_DATA_TIMEOUT_SECONDS` | `10` | `int` |
| `max_symbols_per_batch` | `DEFI_MAX_SYMBOLS_PER_BATCH` | `100` | `int` |
| `coingecko_api_key` | `DEFI_COINGECKO_API_KEY` | `None` | `SecretStr` |
| `cmc_api_key` | `DEFI_CMC_API_KEY` | `None` | `SecretStr` |
| `ofac_api_key` | `DEFI_OFAC_API_KEY` | `None` | `SecretStr` |

#### Modelo de segurança das chaves de API

- As chaves de API (`coingecko_api_key`, `cmc_api_key`, `ofac_api_key`) são declaradas como `Optional[SecretStr]`.
- O Pydantic mascara seus valores como `SecretStr('**********')` em qualquer `repr()`, `str()` ou saída de log — sem código customizado.
- As chaves pertencem ao **operador da plataforma**, não aos usuários finais. Um único conjunto de chaves atende toda a base de assinantes de forma transparente.
- As chaves são opcionais: o serviço sobe sem elas (free-tier ou fallback mock). Defina-as em produção apenas via secrets manager ou injeção de segredos no CI/CD — nunca em arquivos `.env` versionados.

#### Configuração dos campos não-secretos em produção

```bash
DEFI_REDIS_URL=redis://seu-redis:6379/0
DEFI_QUOTE_CACHE_TTL_SECONDS=30
DEFI_HISTORY_CACHE_TTL_SECONDS=300
DEFI_MARKET_DATA_TIMEOUT_SECONDS=10
DEFI_MAX_SYMBOLS_PER_BATCH=100
```

As chaves secretas devem ser injetadas em tempo de deploy via secrets de ambiente — nunca commitadas em arquivos `.env` no controle de versão. Consulte `.env.example` para os nomes das variáveis.

---

## Fronteiras regulatórias

Custo de licença financeira zero não é custo zero de operação. Como empresa de tecnologia, a plataforma mantém:

- **Triagem de sanções / OFAC** — a plataforma não serve, de forma consciente, pessoas ou jurisdições sancionadas.
- **Termos de Uso** — deixando claro que o cliente é o operador e o responsável.
- **Obrigações de proteção de dados** aplicáveis a qualquer produto de software.
- **Templates de contrato auditados** — versionamento imutável, trilha de auditoria completa de qual versão do template foi implantada, por quem e quando.

O que a plataforma deliberadamente **não faz**: guardar fundos de clientes, guardar chaves de clientes, rotear valor por contas da empresa, executar ordens discricionárias ou fornecer recomendações personalizadas de investimento.
