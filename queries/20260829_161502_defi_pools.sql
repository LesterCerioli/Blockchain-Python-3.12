-- ============================================================
-- Migração 2/4: Tabela de Pools de Liquidez
-- ============================================================
-- Obs: coluna 'id' é UUID v4 PRIMARY KEY
-- ============================================================

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

-- Índice para busca por tokens e chain
CREATE INDEX IF NOT EXISTS pools_token_chain_idx ON pools(chain_id, token0_address, token1_address);

-- Comentário: Tabela de pools de liquidez (Uniswap V2, V3, etc.)
-- Relacionada a: IPoolRepository, QuoteService.get_quote()