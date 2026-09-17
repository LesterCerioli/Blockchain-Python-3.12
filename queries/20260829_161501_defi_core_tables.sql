
CREATE TABLE IF NOT EXISTS tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address VARCHAR(255) NOT NULL UNIQUE,
    symbol VARCHAR(32) NOT NULL,
    name VARCHAR(128) NOT NULL,
    decimals INTEGER NOT NULL DEFAULT 18,
    chain_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


CREATE UNIQUE INDEX IF NOT EXISTS tokens_symbol_chain_idx ON tokens(symbol, chain_id);


CREATE TABLE IF NOT EXISTS pools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address VARCHAR(255) NOT NULL UNIQUE,
    token0_address VARCHAR(255) NOT NULL,
    token1_address VARCHAR(255) NOT NULL,
    fee_bps INTEGER NOT NULL DEFAULT 30,
    protocol VARCHAR(64) NOT NULL,
    chain_id INTEGER NOT NULL DEFAULT 1,
    liquidity BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS pools_token_chain_idx ON pools(chain_id, token0_address, token1_address);


CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pool_id UUID NOT NULL REFERENCES pools(id) ON DELETE CASCADE,
    owner VARCHAR(255) NOT NULL,
    liquidity BIGINT NOT NULL DEFAULT 0,
    amount0 BIGINT NOT NULL DEFAULT 0,
    amount1 BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS positions_pool_owner_idx ON positions(pool_id, owner);


CREATE TABLE IF NOT EXISTS ohlcv_candles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(32) NOT NULL,
    interval VARCHAR(16) NOT NULL,
    open_time TIMESTAMP WITH TIME ZONE NOT NULL,
    open DECIMAL(78, 80) NOT NULL,
    high DECIMAL(78, 80) NOT NULL,
    low DECIMAL(78, 80) NOT NULL,
    close DECIMAL(78, 80) NOT NULL,
    volume DECIMAL(78, 80) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS ohlcv_symbol_interval_idx ON ohlcv_candles(symbol, interval);
CREATE INDEX IF NOT EXISTS ohlcv_time_idx ON ohlcv_candles(open_time);
CREATE INDEX IF NOT EXISTS ohlcv_symbol_time_idx ON ohlcv_candles(symbol, open_time DESC);

