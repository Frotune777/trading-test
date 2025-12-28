-- Migration 008: Add Monitoring and Observability Tables
-- Created: 2025-12-29
-- Description: Latency tracking, API traffic, error logs, P&L snapshots, and system health

-- Latency metrics table
CREATE TABLE IF NOT EXISTS latency_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    latency_ms FLOAT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_id INTEGER REFERENCES users(id),
    metadata JSONB
);

-- Indexes for latency_metrics
CREATE INDEX IF NOT EXISTS ix_latency_type_timestamp ON latency_metrics(metric_type, timestamp);
CREATE INDEX IF NOT EXISTS ix_latency_operation_timestamp ON latency_metrics(operation, timestamp);
CREATE INDEX IF NOT EXISTS idx_latency_metrics_timestamp ON latency_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_latency_metrics_user_id ON latency_metrics(user_id);

-- API traffic table
CREATE TABLE IF NOT EXISTS api_traffic (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms FLOAT NOT NULL,
    user_id INTEGER REFERENCES users(id),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for api_traffic
CREATE INDEX IF NOT EXISTS ix_traffic_endpoint_timestamp ON api_traffic(endpoint, timestamp);
CREATE INDEX IF NOT EXISTS ix_traffic_status_timestamp ON api_traffic(status_code, timestamp);
CREATE INDEX IF NOT EXISTS ix_traffic_user_timestamp ON api_traffic(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_api_traffic_endpoint ON api_traffic(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_traffic_status_code ON api_traffic(status_code);
CREATE INDEX IF NOT EXISTS idx_api_traffic_timestamp ON api_traffic(timestamp);

-- Error logs table
CREATE TABLE IF NOT EXISTS error_logs (
    id SERIAL PRIMARY KEY,
    error_type VARCHAR(100) NOT NULL,
    error_message VARCHAR(1000) NOT NULL,
    stack_trace VARCHAR(5000),
    endpoint VARCHAR(200),
    user_id INTEGER REFERENCES users(id),
    severity VARCHAR(20) NOT NULL DEFAULT 'ERROR',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB
);

-- Indexes for error_logs
CREATE INDEX IF NOT EXISTS ix_error_type_timestamp ON error_logs(error_type, timestamp);
CREATE INDEX IF NOT EXISTS ix_error_severity_timestamp ON error_logs(severity, timestamp);
CREATE INDEX IF NOT EXISTS idx_error_logs_error_type ON error_logs(error_type);
CREATE INDEX IF NOT EXISTS idx_error_logs_endpoint ON error_logs(endpoint);
CREATE INDEX IF NOT EXISTS idx_error_logs_user_id ON error_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_error_logs_severity ON error_logs(severity);
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs(timestamp);

-- P&L snapshots table
CREATE TABLE IF NOT EXISTS pnl_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    realized_pnl FLOAT NOT NULL DEFAULT 0.0,
    unrealized_pnl FLOAT NOT NULL DEFAULT 0.0,
    total_pnl FLOAT NOT NULL DEFAULT 0.0,
    day_pnl FLOAT NOT NULL DEFAULT 0.0,
    positions_count INTEGER NOT NULL DEFAULT 0,
    trades_count INTEGER NOT NULL DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for pnl_snapshots
CREATE INDEX IF NOT EXISTS ix_pnl_user_timestamp ON pnl_snapshots(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_pnl_snapshots_user_id ON pnl_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_pnl_snapshots_timestamp ON pnl_snapshots(timestamp);

-- Trade performance table
CREATE TABLE IF NOT EXISTS trade_performance (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    symbol VARCHAR(50) NOT NULL,
    strategy_name VARCHAR(100),
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_time TIMESTAMP WITH TIME ZONE,
    entry_price FLOAT NOT NULL,
    exit_price FLOAT,
    quantity INTEGER NOT NULL,
    pnl FLOAT,
    pnl_percent FLOAT,
    holding_time_minutes INTEGER,
    trade_type VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN'
);

-- Indexes for trade_performance
CREATE INDEX IF NOT EXISTS ix_trade_user_symbol ON trade_performance(user_id, symbol);
CREATE INDEX IF NOT EXISTS ix_trade_strategy_status ON trade_performance(strategy_name, status);
CREATE INDEX IF NOT EXISTS ix_trade_entry_time ON trade_performance(entry_time);
CREATE INDEX IF NOT EXISTS idx_trade_performance_user_id ON trade_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_trade_performance_symbol ON trade_performance(symbol);
CREATE INDEX IF NOT EXISTS idx_trade_performance_strategy_name ON trade_performance(strategy_name);
CREATE INDEX IF NOT EXISTS idx_trade_performance_status ON trade_performance(status);

-- System health table
CREATE TABLE IF NOT EXISTS system_health (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    unit VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'HEALTHY',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB
);

-- Indexes for system_health
CREATE INDEX IF NOT EXISTS ix_health_metric_timestamp ON system_health(metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_system_health_metric_name ON system_health(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_health_timestamp ON system_health(timestamp);

-- Comments
COMMENT ON TABLE latency_metrics IS 'Track operation latency metrics for performance monitoring';
COMMENT ON TABLE api_traffic IS 'Track API usage and traffic patterns';
COMMENT ON TABLE error_logs IS 'Track errors and exceptions for debugging';
COMMENT ON TABLE pnl_snapshots IS 'Real-time P&L snapshots for risk management';
COMMENT ON TABLE trade_performance IS 'Per-trade performance metrics for strategy analysis';
COMMENT ON TABLE system_health IS 'System health metrics for infrastructure monitoring';

COMMENT ON COLUMN latency_metrics.metric_type IS 'Type: order_execution, api_call, websocket';
COMMENT ON COLUMN error_logs.severity IS 'Severity: DEBUG, INFO, WARNING, ERROR, CRITICAL';
COMMENT ON COLUMN trade_performance.trade_type IS 'Trade type: LONG or SHORT';
COMMENT ON COLUMN trade_performance.status IS 'Status: OPEN or CLOSED';
COMMENT ON COLUMN system_health.status IS 'Status: HEALTHY, WARNING, or CRITICAL';
