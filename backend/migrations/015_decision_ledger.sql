-- Migration: Decision Ledger with Causal Explainability
-- Immutable records of all trading decisions

-- Decision Ledger Table
CREATE TABLE IF NOT EXISTS decision_ledger (
    id SERIAL PRIMARY KEY,
    decision_id VARCHAR(50) UNIQUE NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Context
    strategy_id INTEGER REFERENCES strategies(id),
    symbol VARCHAR(50) NOT NULL,
    mode VARCHAR(20) NOT NULL,  -- DRY_RUN, LIVE, BACKTEST
    user_id VARCHAR(255) NOT NULL,
    
    -- Final Decision
    final_decision VARCHAR(10) NOT NULL,  -- BUY, SELL, HOLD
    conviction INTEGER NOT NULL,  -- 0-100
    position_size INTEGER,
    
    -- JSON Fields
    inputs JSONB NOT NULL,
    weights JSONB NOT NULL,
    risk_checks JSONB NOT NULL,
    causal_graph JSONB NOT NULL,
    output_details JSONB,
    
    -- Execution Results
    executed BOOLEAN DEFAULT FALSE,
    execution_price DECIMAL(10, 2),
    execution_time TIMESTAMP,
    execution_status VARCHAR(20),
    
    -- Performance Tracking
    actual_pnl DECIMAL(15, 2),
    exit_price DECIMAL(10, 2),
    exit_time TIMESTAMP,
    was_correct BOOLEAN,
    
    -- Metadata
    notes TEXT,
    tags JSONB DEFAULT '[]'
);

CREATE INDEX idx_decision_ledger_decision_id ON decision_ledger(decision_id);
CREATE INDEX idx_decision_ledger_timestamp ON decision_ledger(timestamp);
CREATE INDEX idx_decision_ledger_strategy ON decision_ledger(strategy_id);
CREATE INDEX idx_decision_ledger_symbol ON decision_ledger(symbol);
CREATE INDEX idx_decision_ledger_user ON decision_ledger(user_id);
CREATE INDEX idx_decision_ledger_mode ON decision_ledger(mode);

-- Causal Contributions Table
CREATE TABLE IF NOT EXISTS causal_contributions (
    id SERIAL PRIMARY KEY,
    decision_id VARCHAR(50) REFERENCES decision_ledger(decision_id) NOT NULL,
    
    -- Cause details
    cause_type VARCHAR(50) NOT NULL,  -- INDICATOR, REGIME, ML, FUNDAMENTAL
    cause_name VARCHAR(100) NOT NULL,
    cause_value VARCHAR(100),
    
    -- Effect
    effect_description VARCHAR(255) NOT NULL,
    effect_magnitude FLOAT NOT NULL,
    
    -- Confidence
    confidence FLOAT NOT NULL,  -- 0.0 - 1.0
    conviction_contribution FLOAT NOT NULL,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_causal_contributions_decision ON causal_contributions(decision_id);
CREATE INDEX idx_causal_contributions_type ON causal_contributions(cause_type);

-- Decision Outcomes Table
CREATE TABLE IF NOT EXISTS decision_outcomes (
    id SERIAL PRIMARY KEY,
    decision_id VARCHAR(50) UNIQUE REFERENCES decision_ledger(decision_id) NOT NULL,
    
    -- Outcome metrics
    holding_period_hours FLOAT,
    max_favorable_excursion DECIMAL(10, 2),
    max_adverse_excursion DECIMAL(10, 2),
    
    -- Accuracy
    prediction_accuracy FLOAT,
    conviction_calibration FLOAT,
    
    -- Causal validation
    top_causes_validated JSONB,
    
    -- Learning
    lessons_learned TEXT,
    should_adjust_weights BOOLEAN DEFAULT FALSE,
    
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_decision_outcomes_decision ON decision_outcomes(decision_id);
