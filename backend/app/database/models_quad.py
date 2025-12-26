"""
QUAD Analytics Database Models
Pydantic and SQLAlchemy models for QUAD analytics
"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

Base = declarative_base()


# ==================== Enums ====================

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class AlertType(str, Enum):
    CONVICTION_ABOVE = "CONVICTION_ABOVE"
    CONVICTION_BELOW = "CONVICTION_BELOW"
    PILLAR_DRIFT = "PILLAR_DRIFT"
    SIGNAL_CHANGE = "SIGNAL_CHANGE"
    PREDICTION_CONFIDENCE_LOW = "PREDICTION_CONFIDENCE_LOW"


# ==================== SQLAlchemy Models ====================

class QUADDecision(Base):
    """QUAD decision record"""
    __tablename__ = "quad_decisions"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    conviction = Column(Integer, nullable=False)
    signal = Column(String(10), nullable=False)
    
    # Pillar scores
    trend_score = Column(Integer)
    momentum_score = Column(Integer)
    volatility_score = Column(Integer)
    liquidity_score = Column(Integer)
    sentiment_score = Column(Integer)
    regime_score = Column(Integer)
    
    # Additional data
    reasoning_summary = Column(Text)
    current_price = Column(DECIMAL(10, 2))
    volume = Column(Integer)
    meta_data = Column(JSON)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class QUADPrediction(Base):
    """QUAD conviction prediction"""
    __tablename__ = "quad_predictions"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    predicted_conviction = Column(Integer, nullable=False)
    confidence_interval_low = Column(Integer)
    confidence_interval_high = Column(Integer)
    
    model_version = Column(String(50))
    model_type = Column(String(50))
    accuracy_score = Column(DECIMAL(5, 4))
    
    prediction_days = Column(Integer, default=7)
    features_used = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class QUADAlert(Base):
    """QUAD alert configuration"""
    __tablename__ = "quad_alerts"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    user_id = Column(String(50))
    
    alert_type = Column(String(50), nullable=False)
    threshold = Column(Integer)
    pillar_name = Column(String(20))
    
    active = Column(Boolean, default=True)
    triggered_at = Column(DateTime)
    conviction_value = Column(Integer)
    message = Column(Text)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    
    channels = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QUADPillarCorrelation(Base):
    """Pillar correlation analysis"""
    __tablename__ = "quad_pillar_correlations"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    pillar1 = Column(String(20), nullable=False)
    pillar2 = Column(String(20), nullable=False)
    correlation = Column(DECIMAL(5, 4), nullable=False)
    p_value = Column(DECIMAL(10, 8))
    
    sample_size = Column(Integer)
    days_analyzed = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class QUADSignalAccuracy(Base):
    """Signal accuracy tracking"""
    __tablename__ = "quad_signal_accuracy"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    decision_id = Column(Integer, ForeignKey('quad_decisions.id'))
    
    signal = Column(String(10), nullable=False)
    conviction = Column(Integer, nullable=False)
    signal_date = Column(DateTime, nullable=False)
    
    evaluation_date = Column(DateTime)
    price_at_signal = Column(DECIMAL(10, 2))
    price_at_evaluation = Column(DECIMAL(10, 2))
    price_change_percent = Column(DECIMAL(10, 4))
    
    correct = Column(Boolean)
    profit_loss = Column(DECIMAL(10, 2))
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== Pydantic Models ====================

class PillarScores(BaseModel):
    """Pillar scores"""
    trend: int = Field(..., ge=0, le=100)
    momentum: int = Field(..., ge=0, le=100)
    volatility: int = Field(..., ge=0, le=100)
    liquidity: int = Field(..., ge=0, le=100)
    sentiment: int = Field(..., ge=0, le=100)
    regime: int = Field(..., ge=0, le=100)


class QUADDecisionCreate(BaseModel):
    """Create QUAD decision"""
    symbol: str
    conviction: int = Field(..., ge=0, le=100)
    signal: SignalType
    pillars: PillarScores
    reasoning_summary: Optional[str] = None
    current_price: Optional[float] = None
    volume: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = None


class QUADDecisionResponse(BaseModel):
    """QUAD decision response"""
    id: int
    symbol: str
    timestamp: datetime
    conviction: int
    signal: str
    pillars: PillarScores
    reasoning_summary: Optional[str]
    current_price: Optional[float]
    volume: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConvictionTimelinePoint(BaseModel):
    """Single point in conviction timeline"""
    timestamp: datetime
    conviction: int
    signal: str


class ConvictionTimeline(BaseModel):
    """Conviction timeline"""
    symbol: str
    historical: List[ConvictionTimelinePoint]
    predicted: Optional[List[ConvictionTimelinePoint]] = None
    volatility: Optional[float] = None


class PillarDrift(BaseModel):
    """Pillar drift analysis"""
    pillar: str
    previous_score: int
    current_score: int
    delta: int
    percent_change: float
    previous_bias: str
    current_bias: str
    significant: bool  # True if abs(delta) > 15


class PillarDriftAnalysis(BaseModel):
    """Complete pillar drift analysis"""
    symbol: str
    current_timestamp: datetime
    previous_timestamp: datetime
    drifts: List[PillarDrift]
    total_drift: int  # Sum of absolute deltas


class QUADPredictionResponse(BaseModel):
    """QUAD prediction response"""
    symbol: str
    predicted_conviction: int
    confidence_low: int
    confidence_high: int
    accuracy: float
    model_version: str
    prediction_days: int
    timestamp: datetime


class CorrelationPair(BaseModel):
    """Pillar correlation pair"""
    pillar1: str
    pillar2: str
    correlation: float
    p_value: Optional[float]
    significance: str  # 'strong', 'moderate', 'weak'


class CorrelationMatrix(BaseModel):
    """Correlation matrix"""
    symbol: str
    calculated_at: datetime
    correlations: List[CorrelationPair]
    sample_size: int
    days_analyzed: int


class QUADAlertCreate(BaseModel):
    """Create QUAD alert"""
    symbol: str
    alert_type: AlertType
    threshold: Optional[int] = None
    pillar_name: Optional[str] = None
    channels: List[str] = ['websocket']


class QUADAlertResponse(BaseModel):
    """QUAD alert response"""
    id: int
    symbol: str
    alert_type: str
    threshold: Optional[int]
    pillar_name: Optional[str]
    active: bool
    triggered_at: Optional[datetime]
    message: Optional[str]
    channels: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SignalAccuracyMetrics(BaseModel):
    """Signal accuracy metrics"""
    symbol: str
    total_signals: int
    correct_signals: int
    win_rate: float
    avg_conviction_winning: float
    avg_conviction_losing: float
    total_profit_loss: float
    best_signal: Optional[Dict[str, Any]]
    worst_signal: Optional[Dict[str, Any]]
