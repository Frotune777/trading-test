-- ============================================================
-- QUAD DECISIONS V2 (Institutional Grade)
-- ============================================================

-- Institutional QUAD decisions with probability distributions
CREATE TABLE IF NOT EXISTS quad_decisions_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- PILLAR 1: Price & Market Structure
    p1_prob_strong_bullish REAL,
    p1_prob_bullish REAL,
    p1_prob_neutral REAL,
    p1_prob_bearish REAL,
    p1_prob_strong_bearish REAL,
    p1_primary_bias TEXT,
    p1_confidence REAL,
    p1_health TEXT,
    p1_health_message TEXT,
    p1_features JSON,
    p1_version TEXT,
    
    -- PILLAR 2: Institutional Flow
    p2_prob_strong_bullish REAL,
    p2_prob_bullish REAL,
    p2_prob_neutral REAL,
    p2_prob_bearish REAL,
    p2_prob_strong_bearish REAL,
    p2_primary_bias TEXT,
    p2_confidence REAL,
    p2_health TEXT,
    p2_health_message TEXT,
    p2_features JSON,
    p2_version TEXT,
    
    -- PILLAR 3: Derivatives & Positioning
    p3_prob_strong_bullish REAL,
    p3_prob_bullish REAL,
    p3_prob_neutral REAL,
    p3_prob_bearish REAL,
    p3_prob_strong_bearish REAL,
    p3_primary_bias TEXT,
    p3_confidence REAL,
    p3_health TEXT,
    p3_health_message TEXT,
    p3_features JSON,
    p3_version TEXT,
    
    -- PILLAR 4: Risk & Regime Context
    p4_prob_strong_bullish REAL,
    p4_prob_bullish REAL,
    p4_prob_neutral REAL,
    p4_prob_bearish REAL,
    p4_prob_strong_bearish REAL,
    p4_primary_bias TEXT,
    p4_confidence REAL,
    p4_health TEXT,
    p4_health_message TEXT,
    p4_features JSON,
    p4_version TEXT,
    
    -- PILLAR 5: Fundamental / Thematic
    p5_prob_strong_bullish REAL,
    p5_prob_bullish REAL,
    p5_prob_neutral REAL,
    p5_prob_bearish REAL,
    p5_prob_strong_bearish REAL,
    p5_primary_bias TEXT,
    p5_confidence REAL,
    p5_health TEXT,
    p5_health_message TEXT,
    p5_features JSON,
    p5_version TEXT,
    
    -- PILLAR 6: Execution & Feasibility
    p6_prob_strong_bullish REAL,
    p6_prob_bullish REAL,
    p6_prob_neutral REAL,
    p6_prob_bearish REAL,
    p6_prob_strong_bearish REAL,
    p6_primary_bias TEXT,
    p6_confidence REAL,
    p6_health TEXT,
    p6_health_message TEXT,
    p6_features JSON,
    p6_version TEXT,
    
    -- AGGREGATED DECISION
    final_prob_strong_bullish REAL,
    final_prob_bullish REAL,
    final_prob_neutral REAL,
    final_prob_bearish REAL,
    final_prob_strong_bearish REAL,
    final_bias TEXT,
    final_confidence REAL,
    base_confidence REAL,  -- Before conviction capping
    
    -- VALIDITY & EXECUTION
    validity TEXT,  -- VALID, DEGRADED, INVALID
    blocking_reasons JSON,
    is_executable BOOLEAN,
    execution_risk_flags JSON,
    
    -- RISK ENVELOPE
    max_position_size REAL,
    stop_loss_pct REAL,
    take_profit_pct REAL,
    max_hold_days INTEGER,
    expected_value REAL,
    
    -- PILLAR METADATA
    pillar_weights JSON,
    all_risk_flags JSON,
    num_healthy_pillars INTEGER,
    num_degraded_pillars INTEGER,
    num_failed_pillars INTEGER,
    
    -- AUDIT TRAIL
    data_sources_used JSON,
    feature_versions JSON,
    computation_time_ms INTEGER,
    
    FOREIGN KEY (symbol) REFERENCES companies(symbol)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_quad_v2_symbol_timestamp ON quad_decisions_v2(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_quad_v2_timestamp ON quad_decisions_v2(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_quad_v2_validity ON quad_decisions_v2(validity);
CREATE INDEX IF NOT EXISTS idx_quad_v2_executable ON quad_decisions_v2(is_executable);
