-- PKScreener Integration Tables
-- Created: 2026-01-09

-- Custom Stock Lists Table
CREATE TABLE IF NOT EXISTS custom_stock_lists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    stocks TEXT[] NOT NULL,  -- ARRAY of symbols
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- PKScreener Results Table
CREATE TABLE IF NOT EXISTS pkscreener_results (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(50),
    index_name VARCHAR(50),
    strategy_name VARCHAR(100),
    results JSONB,
    file_path TEXT,
    scan_time TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pkscreener_results_scan_id ON pkscreener_results(scan_id);
CREATE INDEX IF NOT EXISTS idx_pkscreener_results_time ON pkscreener_results(scan_time DESC);
CREATE INDEX IF NOT EXISTS idx_custom_stock_lists_name ON custom_stock_lists(name);
