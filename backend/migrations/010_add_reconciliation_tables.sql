-- Migration 010: Add Position Reconciliation Tables
-- Description: Creates tables for tracking broker position snapshots and reconciliation runs.

-- Position Snapshots
CREATE TABLE IF NOT EXISTS position_snapshots (
    id SERIAL PRIMARY KEY,
    broker VARCHAR(20) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    average_price DECIMAL(10, 2),
    current_price DECIMAL(10, 2),
    pnl DECIMAL(12, 2),
    product_type VARCHAR(10),
    snapshot_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_position_snapshots_broker ON position_snapshots(broker);
CREATE INDEX IF NOT EXISTS idx_position_snapshots_symbol ON position_snapshots(symbol);
CREATE INDEX IF NOT EXISTS idx_position_snapshots_time ON position_snapshots(snapshot_time);

-- Position Discrepancies
CREATE TABLE IF NOT EXISTS position_discrepancies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    broker VARCHAR(20) NOT NULL,
    local_quantity INTEGER,
    broker_quantity INTEGER,
    difference INTEGER NOT NULL,
    local_avg_price DECIMAL(10, 2),
    broker_avg_price DECIMAL(10, 2),
    detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    resolution_action TEXT,
    resolution_method VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_pos_discrepancy_symbol ON position_discrepancies(symbol);
CREATE INDEX IF NOT EXISTS idx_pos_discrepancy_broker ON position_discrepancies(broker);
CREATE INDEX IF NOT EXISTS idx_pos_discrepancy_resolved ON position_discrepancies(resolved);

-- Reconciliation Runs
CREATE TABLE IF NOT EXISTS reconciliation_runs (
    id SERIAL PRIMARY KEY,
    run_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    brokers_checked VARCHAR[] NOT NULL,
    total_positions INTEGER DEFAULT 0,
    discrepancies_found INTEGER DEFAULT 0,
    auto_corrections INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    duration_ms INTEGER,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_recon_runs_time ON reconciliation_runs(run_time);
CREATE INDEX IF NOT EXISTS idx_recon_runs_status ON reconciliation_runs(status);

COMMENT ON TABLE position_snapshots IS 'Snapshots of positions fetched from brokers';
COMMENT ON TABLE position_discrepancies IS 'Differences detected between local and broker positions';
COMMENT ON TABLE reconciliation_runs IS 'Log of reconciliation job executions';
