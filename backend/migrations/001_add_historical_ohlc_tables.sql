-- Database Migration: Historical OHLC and Data Fetch Logging
-- Created: 2025-12-26
-- Purpose: Add tables for historical data storage and audit logging

-- Table: historical_ohlc
-- Stores time-series OHLC candlestick data with quality metrics
CREATE TABLE IF NOT EXISTS historical_ohlc (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL DEFAULT 'NSE',
    interval VARCHAR(5) NOT NULL,  -- 1m, 5m, 15m, 30m, 1h, 1d
    timestamp TIMESTAMPTZ NOT NULL,
    
    -- OHLCV data
    open NUMERIC(12, 2),
    high NUMERIC(12, 2),
    low NUMERIC(12, 2),
    close NUMERIC(12, 2),
    volume BIGINT,
    
    -- Metadata
    source VARCHAR(20) NOT NULL,  -- 'openalgo', 'nse', 'yahoo'
    quality_score NUMERIC(3, 2),  -- 0.00-1.00
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT uix_symbol_interval_timestamp UNIQUE (symbol, exchange, interval, timestamp)
);

-- Indexes for historical_ohlc
CREATE INDEX IF NOT EXISTS idx_ohlc_lookup ON historical_ohlc(symbol, interval, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ohlc_quality ON historical_ohlc(symbol, quality_score);
CREATE INDEX IF NOT EXISTS idx_ohlc_timestamp ON historical_ohlc(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ohlc_symbol_exchange ON historical_ohlc(symbol, exchange);

-- Table: data_fetch_log
-- Audit log for all data fetching operations
CREATE TABLE IF NOT EXISTS data_fetch_log (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    interval VARCHAR(5) NOT NULL,
    source VARCHAR(20) NOT NULL,
    
    -- Request details
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    period VARCHAR(10),  -- 1d, 1mo, 1y, etc.
    
    -- Response details
    success INTEGER NOT NULL,  -- 1 = success, 0 = failure
    candles_fetched INTEGER,
    error_message VARCHAR(500),
    elapsed_ms INTEGER,
    
    -- Quality metrics
    quality_score NUMERIC(3, 2),
    quality_issues TEXT  -- JSON string
);

-- Indexes for data_fetch_log
CREATE INDEX IF NOT EXISTS idx_fetch_log_time ON data_fetch_log(requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_fetch_log_symbol ON data_fetch_log(symbol, requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_fetch_log_success ON data_fetch_log(success, requested_at DESC);

-- Comments for documentation
COMMENT ON TABLE historical_ohlc IS 'Historical OHLC candlestick data with quality validation';
COMMENT ON TABLE data_fetch_log IS 'Audit log for data pipeline operations (Rule #33-34 compliance)';

COMMENT ON COLUMN historical_ohlc.quality_score IS 'Data quality score 0.00-1.00 from validation checks';
COMMENT ON COLUMN historical_ohlc.source IS 'Data source: openalgo, nse, or yahoo';
COMMENT ON COLUMN data_fetch_log.success IS '1 for successful fetch, 0 for failure';
COMMENT ON COLUMN data_fetch_log.quality_issues IS 'JSON array of quality validation issues';

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE ON historical_ohlc TO your_app_user;
-- GRANT SELECT, INSERT ON data_fetch_log TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE historical_ohlc_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE data_fetch_log_id_seq TO your_app_user;
