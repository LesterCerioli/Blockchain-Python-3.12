
CREATE TABLE IF NOT EXISTS ohlcv_candles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(32) NOT NULL,
    interval VARCHAR(16) NOT NULL,
    open_time TIMESTAMP WITH TIME ZONE NOT NULL,
    open DECIMAL(38, 18) NOT NULL,
    high DECIMAL(38, 18) NOT NULL,
    low DECIMAL(38, 18) NOT NULL,
    close DECIMAL(38, 18) NOT NULL,
    volume DECIMAL(38, 18) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS ohlcv_symbol_interval_idx ON ohlcv_candles(symbol, interval);
CREATE INDEX IF NOT EXISTS ohlcv_time_idx ON ohlcv_candles(open_time);
CREATE INDEX IF NOT EXISTS ohlcv_symbol_time_idx ON ohlcv_candles(symbol, open_time DESC);

