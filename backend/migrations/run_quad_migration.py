"""
Run QUAD Analytics SQLite Migration
Creates tables for QUAD v1.1 Analytics
"""

import sqlite3
import sys
from pathlib import Path

# Connect to database
db_path = Path(__file__).parent.parent / "stock_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print(f"Connected to {db_path}")

# Create tables
tables_sql = """
-- QUAD Decisions Table
CREATE TABLE IF NOT EXISTS quad_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    conviction INTEGER NOT NULL CHECK (conviction >= 0 AND conviction <= 100),
    signal TEXT NOT NULL CHECK (signal IN ('BUY', 'SELL', 'HOLD')),
    
    trend_score INTEGER CHECK (trend_score >= 0 AND trend_score <= 100),
    momentum_score INTEGER CHECK (momentum_score >= 0 AND momentum_score <= 100),
    volatility_score INTEGER CHECK (volatility_score >= 0 AND volatility_score <= 100),
    liquidity_score INTEGER CHECK (liquidity_score >= 0 AND liquidity_score <= 100),
    sentiment_score INTEGER CHECK (sentiment_score >= 0 AND sentiment_score <= 100),
    regime_score INTEGER CHECK (regime_score >= 0 AND regime_score <= 100),
    
    reasoning_summary TEXT,
    current_price REAL,
    volume INTEGER,
    meta_data TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quad_decisions_symbol ON quad_decisions(symbol);
CREATE INDEX IF NOT EXISTS idx_quad_decisions_timestamp ON quad_decisions(timestamp DESC);

-- QUAD Predictions Table
CREATE TABLE IF NOT EXISTS quad_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    predicted_conviction INTEGER NOT NULL CHECK (predicted_conviction >= 0 AND predicted_conviction <= 100),
    confidence_interval_low INTEGER CHECK (confidence_interval_low >= 0 AND confidence_interval_low <= 100),
    confidence_interval_high INTEGER CHECK (confidence_interval_high >= 0 AND confidence_interval_high <= 100),
    
    model_version TEXT,
    model_type TEXT,
    accuracy_score REAL,
    
    prediction_days INTEGER DEFAULT 7,
    features_used TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quad_predictions_symbol ON quad_predictions(symbol);

-- QUAD Alerts Table
CREATE TABLE IF NOT EXISTS quad_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    user_id TEXT,
    
    alert_type TEXT NOT NULL CHECK (alert_type IN (
        'CONVICTION_ABOVE', 'CONVICTION_BELOW', 
        'PILLAR_DRIFT', 'SIGNAL_CHANGE',
        'PREDICTION_CONFIDENCE_LOW'
    )),
    threshold INTEGER,
    pillar_name TEXT,
    
    active INTEGER DEFAULT 1,
    triggered_at DATETIME,
    conviction_value INTEGER,
    message TEXT,
    acknowledged INTEGER DEFAULT 0,
    acknowledged_at DATETIME,
    
    channels TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quad_alerts_symbol ON quad_alerts(symbol);
CREATE INDEX IF NOT EXISTS idx_quad_alerts_active ON quad_alerts(active);

-- QUAD Pillar Correlations Table
CREATE TABLE IF NOT EXISTS quad_pillar_correlations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    calculated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    pillar1 TEXT NOT NULL,
    pillar2 TEXT NOT NULL,
    correlation REAL NOT NULL,
    p_value REAL,
    
    sample_size INTEGER,
    days_analyzed INTEGER,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quad_correlations_symbol ON quad_pillar_correlations(symbol);

-- QUAD Signal Accuracy Table
CREATE TABLE IF NOT EXISTS quad_signal_accuracy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    decision_id INTEGER REFERENCES quad_decisions(id),
    
    signal TEXT NOT NULL,
    conviction INTEGER NOT NULL,
    signal_date DATETIME NOT NULL,
    
    evaluation_date DATETIME,
    price_at_signal REAL,
    price_at_evaluation REAL,
    price_change_percent REAL,
    
    correct INTEGER,
    profit_loss REAL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quad_accuracy_symbol ON quad_signal_accuracy(symbol);
"""

try:
    # Execute all statements
    cursor.executescript(tables_sql)
    conn.commit()
    
    # Verify tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'quad%'")
    tables = cursor.fetchall()
    
    print("\n✅ Migration successful!")
    print(f"Created {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Migration failed: {e}")
    conn.rollback()
    sys.exit(1)
    
finally:
    conn.close()
