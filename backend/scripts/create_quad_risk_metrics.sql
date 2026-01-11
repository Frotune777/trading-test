-- Create quad_risk_metrics table
CREATE TABLE IF NOT EXISTS quad_risk_metrics (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP NOT NULL,
    var_95_30d DECIMAL(10,4),
    var_99_30d DECIMAL(10,4),
    var_95_60d DECIMAL(10,4),
    var_99_60d DECIMAL(10,4),
    var_95_90d DECIMAL(10,4),
    var_99_90d DECIMAL(10,4),
    beta DECIMAL(10,4),
    beta_30d DECIMAL(10,4),
    beta_60d DECIMAL(10,4),
    beta_252d DECIMAL(10,4),
    sharpe_ratio DECIMAL(10,4),
    sharpe_30d DECIMAL(10,4),
    sharpe_60d DECIMAL(10,4),
    sharpe_252d DECIMAL(10,4),
    volatility DECIMAL(10,4),
    volatility_30d DECIMAL(10,4),
    volatility_60d DECIMAL(10,4),
    volatility_252d DECIMAL(10,4),
    data_points_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quad_risk_metrics_symbol ON quad_risk_metrics(symbol);
