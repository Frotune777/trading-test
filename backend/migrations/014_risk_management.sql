-- Migration: Risk Management Tables
-- Phase 3: Risk Control & Alerts

-- Risk Limits Table
CREATE TABLE IF NOT EXISTS risk_limits (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    
    -- Position limits
    max_positions INTEGER DEFAULT 10,
    max_position_size DECIMAL(15, 2) DEFAULT 100000,
    max_portfolio_value DECIMAL(15, 2) DEFAULT 1000000,
    
    -- Loss limits
    max_daily_loss DECIMAL(15, 2) DEFAULT 50000,
    max_weekly_loss DECIMAL(15, 2) DEFAULT 100000,
    max_drawdown_pct FLOAT DEFAULT 20.0,
    
    -- Concentration limits
    max_sector_concentration_pct FLOAT DEFAULT 30.0,
    max_single_stock_pct FLOAT DEFAULT 10.0,
    
    -- Kill switch
    kill_switch_enabled BOOLEAN DEFAULT FALSE,
    kill_switch_reason VARCHAR(500),
    kill_switch_activated_at TIMESTAMP,
    kill_switch_activated_by VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_user_limits UNIQUE(user_id)
);

CREATE INDEX idx_risk_limits_user ON risk_limits(user_id);

-- Risk Metrics Table
CREATE TABLE IF NOT EXISTS risk_metrics (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- P&L metrics
    total_pnl DECIMAL(15, 2) DEFAULT 0,
    daily_pnl DECIMAL(15, 2) DEFAULT 0,
    weekly_pnl DECIMAL(15, 2) DEFAULT 0,
    unrealized_pnl DECIMAL(15, 2) DEFAULT 0,
    realized_pnl DECIMAL(15, 2) DEFAULT 0,
    
    -- Position metrics
    position_count INTEGER DEFAULT 0,
    total_exposure DECIMAL(15, 2) DEFAULT 0,
    portfolio_value DECIMAL(15, 2) DEFAULT 0,
    
    -- Risk metrics
    current_drawdown_pct FLOAT DEFAULT 0,
    var_95 DECIMAL(15, 2),
    sharpe_ratio FLOAT,
    
    -- Concentration (JSON)
    concentration_by_symbol JSONB DEFAULT '{}',
    concentration_by_sector JSONB DEFAULT '{}',
    
    -- Limit utilization
    position_limit_utilization FLOAT DEFAULT 0,
    daily_loss_limit_utilization FLOAT DEFAULT 0,
    weekly_loss_limit_utilization FLOAT DEFAULT 0
);

CREATE INDEX idx_risk_metrics_user ON risk_metrics(user_id);
CREATE INDEX idx_risk_metrics_timestamp ON risk_metrics(timestamp);

-- Kill Switch Log Table
CREATE TABLE IF NOT EXISTS kill_switch_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_by VARCHAR(255) NOT NULL,
    reason VARCHAR(500) NOT NULL,
    
    -- State at activation
    active_positions INTEGER DEFAULT 0,
    total_pnl DECIMAL(15, 2) DEFAULT 0,
    portfolio_value DECIMAL(15, 2) DEFAULT 0,
    
    -- Deactivation
    deactivated_at TIMESTAMP,
    deactivated_by VARCHAR(255),
    deactivation_reason VARCHAR(500)
);

CREATE INDEX idx_kill_switch_logs_user ON kill_switch_logs(user_id);
CREATE INDEX idx_kill_switch_logs_activated ON kill_switch_logs(activated_at);

-- Alert Log Table
CREATE TABLE IF NOT EXISTS alert_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Alert details
    alert_type VARCHAR(50) NOT NULL,  -- CRITICAL, WARNING, INFO
    category VARCHAR(50) NOT NULL,    -- RISK, DATA, SYSTEM, TRADE
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- Context
    related_symbol VARCHAR(50),
    related_strategy_id INTEGER,
    metadata JSONB DEFAULT '{}',
    
    -- Status
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(255)
);

CREATE INDEX idx_alert_logs_user ON alert_logs(user_id);
CREATE INDEX idx_alert_logs_timestamp ON alert_logs(timestamp);
CREATE INDEX idx_alert_logs_acknowledged ON alert_logs(acknowledged);
CREATE INDEX idx_alert_logs_type ON alert_logs(alert_type);
