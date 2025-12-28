from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

# ==================== ENUMS ====================

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NONE = "NONE"

class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"

class PillarBias(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"

# ==================== CONTRACTS ====================

class AnalysisState(BaseModel):
    """
    Contract: Output of QUAD Reasoning Engine.
    Represents the logical 'opinion' of the system for a specific symbol at a specific time.
    """
    decision_id: str
    symbol: str
    timestamp: datetime
    logical_time: datetime # The time the data represents (OHLCV close time)
    
    primary_signal: SignalType
    conviction_score: float = Field(..., ge=0, le=100)
    
    pillar_outputs: Dict[str, Dict[str, Any]] # Raw pillar scores and health
    regime_context: str
    
    metrics: Dict[str, float] = {} # Parkinson vol, Variance ratio, etc.
    
    class Config:
        frozen = True # Immutable once created

class PositionState(BaseModel):
    """
    Contract: Snapshot of current broker inventory (The Truth).
    Used for P&L reconciliation and exposure tracking.
    """
    symbol: str
    quantity: int
    average_price: float
    ltp: float
    unrealized_pnl: float
    realized_pnl: float
    
    side: str # LONG / SHORT
    broker_timestamp: datetime
    
    metadata: Dict[str, Any] = {}

class RiskState(BaseModel):
    """
    Contract: Current risk headroom and governance context.
    Determines if a trade is ALLOWED or BLOCKED.
    """
    timestamp: datetime
    
    daily_pnl: float
    max_daily_loss_limit: float
    is_kill_switch_active: bool
    
    active_exposure: float
    max_exposure_limit: float
    
    symbol_exposure: Dict[str, float]
    
    can_trade: bool
    block_reasons: List[str] = []

class ExecutionState(BaseModel):
    """
    Contract: Result of an execution attempt.
    """
    request_id: str
    order_id: Optional[str] = None
    symbol: str
    
    status: ExecutionStatus
    filled_quantity: int = 0
    average_fill_price: Optional[float] = None
    
    error_message: Optional[str] = None
    broker_response: Dict[str, Any] = {}
    
    execution_time: datetime
    audit_trail: List[Dict[str, Any]] = []
