-- Migration: Add TA Signal Tracking and Regime Weights
-- Phase 2.3 Enhancement

-- Update quad_user_preferences to include TA specific weights
ALTER TABLE quad_user_preferences ADD COLUMN IF NOT EXISTS ta_weights JSON;

-- Create ta_signal_records table
CREATE TABLE IF NOT EXISTS ta_signal_records (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    signal VARCHAR(10) NOT NULL,
    confidence DECIMAL(5, 4),
    regime VARCHAR(20),
    composite_score DECIMAL(5, 4),
    indicator_scores JSON,
    weights_used JSON,
    price_at_signal DECIMAL(10, 2),
    peak_price_5d DECIMAL(10, 2),
    lowest_price_5d DECIMAL(10, 2),
    is_accurate BOOLEAN,
    final_pnl_pct DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ta_signals_symbol ON ta_signal_records(symbol);

-- Create ta_indicator_performance table
CREATE TABLE IF NOT EXISTS ta_indicator_performance (
    id SERIAL PRIMARY KEY,
    indicator_category VARCHAR(50) NOT NULL,
    regime VARCHAR(50) NOT NULL,
    signals_count INTEGER DEFAULT 0,
    correct_signals INTEGER DEFAULT 0,
    accuracy_rate DECIMAL(5, 4) DEFAULT 0,
    avg_gain DECIMAL(10, 4) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(indicator_category, regime)
);
