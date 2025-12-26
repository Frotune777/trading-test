-- Strategy Management Tables
-- Migration for Phase 2: Strategy Management System

-- Strategies table
CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    webhook_id VARCHAR(36) NOT NULL UNIQUE,
    user_id VARCHAR(50) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT false NOT NULL,
    is_intraday BOOLEAN DEFAULT true NOT NULL,
    trading_mode VARCHAR(10) NOT NULL DEFAULT 'LONG',
    start_time TIME,
    end_time TIME,
    squareoff_time TIME,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Indexes for strategies
CREATE INDEX idx_strategies_webhook_id ON strategies(webhook_id);
CREATE INDEX idx_strategies_user_id ON strategies(user_id);
CREATE INDEX idx_strategies_name ON strategies(name);
CREATE INDEX idx_strategies_is_active ON strategies(is_active);

-- Strategy symbol mappings table
CREATE TABLE IF NOT EXISTS strategy_symbol_mappings (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    product_type VARCHAR(10) NOT NULL,
    broker VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Indexes for symbol mappings
CREATE INDEX idx_symbol_mappings_strategy_id ON strategy_symbol_mappings(strategy_id);
CREATE INDEX idx_symbol_mappings_symbol ON strategy_symbol_mappings(symbol);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE strategies IS 'Webhook-based trading strategies';
COMMENT ON TABLE strategy_symbol_mappings IS 'Symbol mappings for each strategy';
COMMENT ON COLUMN strategies.webhook_id IS 'Unique UUID for webhook endpoint';
COMMENT ON COLUMN strategies.trading_mode IS 'LONG, SHORT, or BOTH';
COMMENT ON COLUMN strategies.start_time IS 'Entry window start time (intraday only)';
COMMENT ON COLUMN strategies.end_time IS 'Entry window end time (intraday only)';
COMMENT ON COLUMN strategies.squareoff_time IS 'Auto-squareoff time (intraday only)';
