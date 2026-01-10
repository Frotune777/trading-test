-- Phase 3: Data Migration - Supplementary Tables

-- Indicator History (Consolidated JSONB storage)
CREATE TABLE IF NOT EXISTS indicator_history (
    id SERIAL PRIMARY KEY,
    ohlc_id INTEGER REFERENCES historical_ohlc(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    interval VARCHAR(5) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    indicators JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for indicator_history
CREATE INDEX IF NOT EXISTS idx_indicator_history_symbol_interval_ts ON indicator_history (symbol, interval, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_indicator_history_ohlc_id ON indicator_history (ohlc_id);

-- Market Bulk Deals
CREATE TABLE IF NOT EXISTS market_bulk_deals (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    order_type VARCHAR(20),
    symbol VARCHAR(20) NOT NULL,
    scrip_name TEXT,
    client_name TEXT,
    buy_sell VARCHAR(10),
    quantity BIGINT,
    price DECIMAL(15,2),
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_market_bulk_deals_symbol_date ON market_bulk_deals (symbol, date DESC);

-- Market Insider Trading
CREATE TABLE IF NOT EXISTS market_insider_trading (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    company TEXT,
    person TEXT,
    category TEXT,
    mode TEXT,
    quantity BIGINT,
    value DECIMAL(15,2),
    transaction_type VARCHAR(20),
    holding_post BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_market_insider_trading_symbol_date ON market_insider_trading (symbol, date DESC);

-- Market FII/DII Activity
CREATE TABLE IF NOT EXISTS market_fii_dii (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    category VARCHAR(20), -- FII, DII
    buy_value DECIMAL(15,2),
    sell_value DECIMAL(15,2),
    net_value DECIMAL(15,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_market_fii_dii_date ON market_fii_dii (date DESC);

-- Ohlcv Sync Status (Migration of ohlcv_metadata)
CREATE TABLE IF NOT EXISTS ohlcv_metadata (
    symbol VARCHAR(20) NOT NULL,
    interval VARCHAR(5) NOT NULL,
    first_date TIMESTAMPTZ,
    last_date TIMESTAMPTZ,
    record_count INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (symbol, interval)
);
