CREATE TABLE IF NOT EXISTS risk_metrics (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP NOT NULL,
    var_95_30d DECIMAL(10, 4),
    var_99_30d DECIMAL(10, 4),
    var_95_60d DECIMAL(10, 4),
    var_99_60d DECIMAL(10, 4),
    beta DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    volatility DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_metrics_symbol ON risk_metrics(symbol);
CREATE INDEX IF NOT EXISTS idx_risk_metrics_calculated_at ON risk_metrics(calculated_at);
