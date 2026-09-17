
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

