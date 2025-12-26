-- Position Reconciliation Tables
-- Migration for Phase 4: Position Reconciliation

-- Position snapshots table
CREATE TABLE IF NOT EXISTS position_snapshots (
    id SERIAL PRIMARY KEY,
    broker VARCHAR(20) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    average_price DECIMAL(10,2),
    current_price DECIMAL(10,2),
    pnl DECIMAL(12,2),
    product_type VARCHAR(10),
    snapshot_time TIMESTAMP DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Indexes for position snapshots
CREATE INDEX idx_position_snapshots_broker ON position_snapshots(broker);
CREATE INDEX idx_position_snapshots_symbol ON position_snapshots(symbol);
CREATE INDEX idx_position_snapshots_snapshot_time ON position_snapshots(snapshot_time);
CREATE INDEX idx_position_snapshots_broker_symbol ON position_snapshots(broker, symbol);

-- Position discrepancies table
CREATE TABLE IF NOT EXISTS position_discrepancies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    broker VARCHAR(20) NOT NULL,
    local_quantity INTEGER,
    broker_quantity INTEGER,
    difference INTEGER NOT NULL,
    local_avg_price DECIMAL(10,2),
    broker_avg_price DECIMAL(10,2),
    detected_at TIMESTAMP DEFAULT NOW() NOT NULL,
    resolved BOOLEAN DEFAULT false NOT NULL,
    resolved_at TIMESTAMP,
    resolution_action TEXT,
    resolution_method VARCHAR(50)
);

-- Indexes for discrepancies
CREATE INDEX idx_discrepancies_symbol ON position_discrepancies(symbol);
CREATE INDEX idx_discrepancies_broker ON position_discrepancies(broker);
CREATE INDEX idx_discrepancies_resolved ON position_discrepancies(resolved);
CREATE INDEX idx_discrepancies_detected_at ON position_discrepancies(detected_at);

-- Reconciliation runs table
CREATE TABLE IF NOT EXISTS reconciliation_runs (
    id SERIAL PRIMARY KEY,
    run_time TIMESTAMP DEFAULT NOW() NOT NULL,
    brokers_checked TEXT[] NOT NULL,
    total_positions INTEGER DEFAULT 0,
    discrepancies_found INTEGER DEFAULT 0,
    auto_corrections INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    duration_ms INTEGER,
    completed_at TIMESTAMP
);

-- Index for reconciliation runs
CREATE INDEX idx_reconciliation_runs_run_time ON reconciliation_runs(run_time);
CREATE INDEX idx_reconciliation_runs_status ON reconciliation_runs(status);

-- Comments
COMMENT ON TABLE position_snapshots IS 'Historical position snapshots from brokers';
COMMENT ON TABLE position_discrepancies IS 'Detected position mismatches between local and broker';
COMMENT ON TABLE reconciliation_runs IS 'Reconciliation job execution history';

COMMENT ON COLUMN position_discrepancies.difference IS 'broker_quantity - local_quantity';
COMMENT ON COLUMN position_discrepancies.resolution_method IS 'AUTO, MANUAL, or IGNORED';
