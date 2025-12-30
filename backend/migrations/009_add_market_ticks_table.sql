-- Database Migration: Market Ticks Storage
-- Created: 2025-12-29
-- Purpose: Add table for persistent tick-level storage

-- Table: market_ticks
-- Stores tick-level market data for high-frequency analysis and auditability
CREATE TABLE IF NOT EXISTS market_ticks (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL DEFAULT 'NSE',
    ltp NUMERIC(12, 2) NOT NULL,
    volume BIGINT,
    oi BIGINT,
    
    -- Time metadata
    timestamp TIMESTAMPTZ NOT NULL,  -- Broker/Feed TS
    received_at TIMESTAMPTZ DEFAULT NOW(), -- Local TS
    
    -- Constraints
    -- We allow multiple ticks at the same timestamp for different symbols
    -- but symbol+exchange+timestamp is typically unique enough for lookups
    CONSTRAINT uix_ticks_lookup UNIQUE (symbol, exchange, timestamp)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ticks_lookup ON market_ticks(symbol, exchange, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ticks_time ON market_ticks(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ticks_received ON market_ticks(received_at DESC);

-- Comments for documentation
COMMENT ON TABLE market_ticks IS 'Persistent tick-level market data storage';
COMMENT ON COLUMN market_ticks.timestamp IS 'Last Traded Price timestamp from the broker/feed';
COMMENT ON COLUMN market_ticks.received_at IS 'Local timestamp when the tick was received by the platform';

-- Permissions
-- GRANT SELECT, INSERT ON market_ticks TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE market_ticks_id_seq TO your_app_user;
