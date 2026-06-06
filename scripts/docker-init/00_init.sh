#!/usr/bin/env bash
# Runs once on first PostgreSQL initialization (empty data volume).
# Creates the cryptobank database used by the DeFi service and applies
# all service migrations so the stack is ready without manual steps.
set -euo pipefail

PGUSER="${POSTGRES_USER:-postgres}"
ETH_DB="${POSTGRES_DB:-fastchainbank}"
DEFI_DB="cryptobank"

echo "[init] Creating database: $DEFI_DB"
psql -v ON_ERROR_STOP=1 --username "$PGUSER" <<-EOSQL
    CREATE DATABASE $DEFI_DB;
    GRANT ALL PRIVILEGES ON DATABASE $DEFI_DB TO "$PGUSER";
EOSQL

echo "[init] Applying Ethereum migrations → $ETH_DB"
psql -v ON_ERROR_STOP=1 --username "$PGUSER" --dbname "$ETH_DB" \
    -f /migrations/ethereum/001_create_eth_providers.sql

echo "[init] Applying DeFi migrations → $DEFI_DB"
psql -v ON_ERROR_STOP=1 --username "$PGUSER" --dbname "$DEFI_DB" \
    -f /migrations/defi/001_create_platform_secrets.sql

echo "[init] Done."
