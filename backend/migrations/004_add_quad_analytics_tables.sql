-- QUAD Analytics Tables Migration
-- Stores QUAD decision history, predictions, and alerts

-- =====================================================
-- QUAD Decisions Table
-- =====================================================
CREATE TABLE IF NOT EXISTS quad_decisions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    conviction INTEGER NOT NULL CHECK (conviction >= 0 AND conviction <= 100),
    signal VARCHAR(10) NOT NULL CHECK (signal IN ('BUY', 'SELL', 'HOLD')),
    
    -- Pillar Scores
    trend_score INTEGER CHECK (trend_score >= 0 AND trend_score <= 100),
    momentum_score INTEGER CHECK (momentum_score >= 0 AND momentum_score <= 100),
    volatility_score INTEGER CHECK (volatility_score >= 0 AND volatility_score <= 100),
    liquidity_score INTEGER CHECK (liquidity_score >= 0 AND liquidity_score <= 100),
    sentiment_score INTEGER CHECK (sentiment_score >= 0 AND sentiment_score <= 100),
    regime_score INTEGER CHECK (regime_score >= 0 AND regime_score <= 100),
    
    -- Additional Data
    reasoning_summary TEXT,
    current_price DECIMAL(10, 2),
    volume BIGINT,
    metadata JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_quad_decisions_symbol ON quad_decisions(symbol);
CREATE INDEX idx_quad_decisions_timestamp ON quad_decisions(timestamp DESC);
CREATE INDEX idx_quad_decisions_symbol_timestamp ON quad_decisions(symbol, timestamp DESC);
CREATE INDEX idx_quad_decisions_signal ON quad_decisions(signal);

-- =====================================================
-- QUAD Predictions Table
-- =====================================================
CREATE TABLE IF NOT EXISTS quad_predictions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Prediction Data
    predicted_conviction INTEGER NOT NULL CHECK (predicted_conviction >= 0 AND predicted_conviction <= 100),
    confidence_interval_low INTEGER CHECK (confidence_interval_low >= 0 AND confidence_interval_low <= 100),
    confidence_interval_high INTEGER CHECK (confidence_interval_high >= 0 AND confidence_interval_high <= 100),
    
    -- Model Info
    model_version VARCHAR(50),
    model_type VARCHAR(50),
    accuracy_score DECIMAL(5, 4),
    
    -- Prediction Horizon
    prediction_days INTEGER DEFAULT 7,
    
    -- Metadata
    features_used JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quad_predictions_symbol ON quad_predictions(symbol);
CREATE INDEX idx_quad_predictions_timestamp ON quad_predictions(timestamp DESC);

-- =====================================================
-- QUAD Alerts Table
-- =====================================================
CREATE TABLE IF NOT EXISTS quad_alerts (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    user_id VARCHAR(50),
    
    -- Alert Configuration
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN (
        'CONVICTION_ABOVE', 'CONVICTION_BELOW', 
        'PILLAR_DRIFT', 'SIGNAL_CHANGE',
        'PREDICTION_CONFIDENCE_LOW'
    )),
    threshold INTEGER,
    pillar_name VARCHAR(20),
    
    -- Alert State
    active BOOLEAN DEFAULT TRUE,
    triggered_at TIMESTAMP,
    conviction_value INTEGER,
    message TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    
    -- Notification Channels
    channels JSONB, -- ['telegram', 'email', 'websocket']
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quad_alerts_symbol ON quad_alerts(symbol);
CREATE INDEX idx_quad_alerts_active ON quad_alerts(active);
CREATE INDEX idx_quad_alerts_user ON quad_alerts(user_id);

-- =====================================================
-- QUAD Pillar Correlations Table
-- =====================================================
CREATE TABLE IF NOT EXISTS quad_pillar_correlations (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Correlation Pairs
    pillar1 VARCHAR(20) NOT NULL,
    pillar2 VARCHAR(20) NOT NULL,
    correlation DECIMAL(5, 4) NOT NULL,
    p_value DECIMAL(10, 8),
    
    -- Sample Info
    sample_size INTEGER,
    days_analyzed INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quad_correlations_symbol ON quad_pillar_correlations(symbol);
CREATE INDEX idx_quad_correlations_calculated ON quad_pillar_correlations(calculated_at DESC);

-- =====================================================
-- QUAD Signal Accuracy Table
-- =====================================================
CREATE TABLE IF NOT EXISTS quad_signal_accuracy (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    decision_id INTEGER REFERENCES quad_decisions(id),
    
    -- Signal Info
    signal VARCHAR(10) NOT NULL,
    conviction INTEGER NOT NULL,
    signal_date TIMESTAMP NOT NULL,
    
    -- Outcome (measured after N days)
    evaluation_date TIMESTAMP,
    price_at_signal DECIMAL(10, 2),
    price_at_evaluation DECIMAL(10, 2),
    price_change_percent DECIMAL(10, 4),
    
    -- Accuracy
    correct BOOLEAN,
    profit_loss DECIMAL(10, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quad_accuracy_symbol ON quad_signal_accuracy(symbol);
CREATE INDEX idx_quad_accuracy_correct ON quad_signal_accuracy(correct);

-- =====================================================
-- Comments
-- =====================================================
COMMENT ON TABLE quad_decisions IS 'Stores all QUAD analysis decisions with pillar scores';
COMMENT ON TABLE quad_predictions IS 'ML-based conviction predictions with confidence intervals';
COMMENT ON TABLE quad_alerts IS 'User-configured alerts for QUAD signals and thresholds';
COMMENT ON TABLE quad_pillar_correlations IS 'Correlation analysis between different pillars';
COMMENT ON TABLE quad_signal_accuracy IS 'Tracks accuracy of QUAD signals over time';
