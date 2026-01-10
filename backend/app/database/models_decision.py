"""
Decision Ledger Models
Immutable records of all trading decisions with causal explainability
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, DECIMAL, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class DecisionLedger(Base):
    """
    Immutable record of every trading decision
    Stores inputs, outputs, weights, risk checks, and causal graph
    """
    __tablename__ = "decision_ledger"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "d-98f2"
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    # Context
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    mode = Column(String(20), nullable=False)  # DRY_RUN, LIVE, BACKTEST
    user_id = Column(String(255), nullable=False, index=True)
    
    # Rule 14: Validity & Context
    validity_window_mins = Column(Integer, default=15, nullable=False)
    strategy_name_snapshot = Column(String(100), nullable=True)
    
    # Final Decision
    final_decision = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    conviction = Column(Integer, nullable=False)  # 0-100
    position_size = Column(Integer, nullable=True)  # Shares to trade
    
    # Inputs (JSON)
    inputs = Column(JSON, nullable=False)
    # {
    #   "price": 3812.5,
    #   "indicators": {"rsi": 29.4, "sma_20": 3791, ...},
    #   "regime": "TRENDING_UP",
    #   "ml": {"prediction": "BUY", "confidence": 0.74, "shadow_mode": true}
    # }
    
    # Pillar Weights
    weights = Column(JSON, nullable=False)
    # {"Q": 0.25, "U": 0.20, "A": 0.30, "D": 0.25}
    
    # Risk Check Results
    risk_checks = Column(JSON, nullable=False)
    # {"position_limit": "PASS", "daily_loss": "PASS", "volatility": "WARN"}
    
    # Causal Graph (JSON array)
    causal_graph = Column(JSON, nullable=False)
    # [
    #   {"cause": "RSI < 30", "effect": "Momentum score +18", "confidence": 0.9},
    #   {"cause": "TRENDING_UP regime", "effect": "Trend weight +14", "confidence": 0.8}
    # ]
    
    # Output Details
    output_details = Column(JSON, nullable=True)
    # {"action": "BUY", "position_size": 120, "limit_price": 3815.0}
    
    # Execution Results (filled after execution)
    executed = Column(Boolean, default=False)
    execution_price = Column(DECIMAL(10, 2), nullable=True)
    execution_time = Column(DateTime, nullable=True)
    execution_status = Column(String(20), nullable=True)  # FILLED, REJECTED, CANCELLED
    
    # Performance Tracking (filled after position closes)
    actual_pnl = Column(DECIMAL(15, 2), nullable=True)
    exit_price = Column(DECIMAL(10, 2), nullable=True)
    exit_time = Column(DateTime, nullable=True)
    was_correct = Column(Boolean, nullable=True)  # Did decision match outcome?
    
    # Metadata
    notes = Column(Text, nullable=True)
    tags = Column(JSON, default=[])  # ["high_conviction", "ml_driven", etc.]
    
    # Relationships
    # strategy = relationship("Strategy", back_populates="decisions")


class CausalContribution(Base):
    """
    Individual causal factors contributing to a decision
    Normalized table for easier querying and analysis
    """
    __tablename__ = "causal_contributions"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(String(50), ForeignKey("decision_ledger.decision_id"), nullable=False, index=True)
    
    # Cause details
    cause_type = Column(String(50), nullable=False, index=True)  # INDICATOR, REGIME, ML, FUNDAMENTAL
    cause_name = Column(String(100), nullable=False)  # "RSI < 30", "TRENDING_UP regime"
    cause_value = Column(String(100), nullable=True)  # Actual value that triggered
    
    # Effect
    effect_description = Column(String(255), nullable=False)  # "Momentum score +18"
    effect_magnitude = Column(Float, nullable=False)  # +18
    
    # Confidence
    confidence = Column(Float, nullable=False)  # 0.0 - 1.0
    
    # Contribution to final conviction
    conviction_contribution = Column(Float, nullable=False)  # How much this added to final conviction
    
    timestamp = Column(DateTime, server_default=func.now())


class DecisionOutcome(Base):
    """
    Post-decision analysis and outcome tracking
    Used for strategy performance evaluation
    """
    __tablename__ = "decision_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(String(50), ForeignKey("decision_ledger.decision_id"), unique=True, nullable=False, index=True)
    
    # Outcome metrics
    holding_period_hours = Column(Float, nullable=True)
    max_favorable_excursion = Column(DECIMAL(10, 2), nullable=True)  # Best price reached
    max_adverse_excursion = Column(DECIMAL(10, 2), nullable=True)  # Worst price reached
    
    # Accuracy
    prediction_accuracy = Column(Float, nullable=True)  # 0.0 - 1.0
    conviction_calibration = Column(Float, nullable=True)  # How well conviction matched outcome
    
    # Causal validation
    top_causes_validated = Column(JSON, nullable=True)  # Which causes were actually important
    # [{"cause": "RSI < 30", "was_valid": true, "actual_impact": 0.85}]
    
    # Learning
    lessons_learned = Column(Text, nullable=True)
    should_adjust_weights = Column(Boolean, default=False)
    
    analyzed_at = Column(DateTime, server_default=func.now())
