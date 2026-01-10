-- ML Pipeline Tables
-- Created: 2026-01-09

-- ML Models Registry
CREATE TABLE IF NOT EXISTS ml_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL,  -- xgboost, random_forest, lstm
    symbol VARCHAR(20),
    model_path TEXT NOT NULL,
    metrics JSONB,
    parameters JSONB,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name, version)
);

-- ML Predictions History
CREATE TABLE IF NOT EXISTS ml_predictions (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES ml_models(id),
    symbol VARCHAR(20) NOT NULL,
    prediction VARCHAR(20) NOT NULL,  -- UP, DOWN, NEUTRAL
    confidence DECIMAL(5,4),
    probabilities JSONB,
    actual_outcome VARCHAR(20),  -- Filled after verification
    predicted_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP
);

-- ML Experiments (MLflow integration)
CREATE TABLE IF NOT EXISTS ml_experiments (
    id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ML Features Cache
CREATE TABLE IF NOT EXISTS ml_features (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    interval VARCHAR(10) NOT NULL,
    features JSONB NOT NULL,
    calculated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, interval)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ml_models_active ON ml_models(is_active, model_type);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_symbol ON ml_predictions(symbol, predicted_at DESC);
CREATE INDEX IF NOT EXISTS idx_ml_features_symbol ON ml_features(symbol, interval);
