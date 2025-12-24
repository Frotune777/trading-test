# app/core/trade_decision.py

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import uuid

@dataclass
class TradeDecision:
    """
    Binding contract between QUAD reasoning and Execution.
    Every execution attempt must have a valid Decision.
    """
    decision_id: str                      # UUID
    strategy_name: str
    strategy_version: str
    symbol: str                           # OpenAlgo format (e.g., NSE:RELIANCE)
    signal: str                           # BUY / SELL / NONE
    confidence_score: float               # 0-100
    decision_ltp: float                   # LTP at the moment of decision
    decision_time: datetime               # Timezone-aware
    valid_till: datetime                  # Hard expiry time
    
    @classmethod
    def create(cls, symbol: str, signal: str, confidence: float, ltp: float, 
               strategy: str = "QUAD_V1", version: str = "1.0.0", tt_seconds: int = 60):
        now = datetime.now()
        from datetime import timedelta
        return cls(
            decision_id=str(uuid.uuid4()),
            strategy_name=strategy,
            strategy_version=version,
            symbol=symbol,
            signal=signal,
            confidence_score=confidence,
            decision_ltp=ltp,
            decision_time=now,
            valid_till=now + timedelta(seconds=tt_seconds)
        )
