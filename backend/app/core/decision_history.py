# app/core/decision_history.py

"""
QUAD v1.1 - Decision History Schema

Purpose: Read-only storage of historical TradeIntent outputs.
Enables conviction stability analysis and audit trail.

CRITICAL CONSTRAINTS:
- Read-only access (no decision mutation)
- No execution logic (pure storage)
- No predictive modeling (historical data only)
- No auto-learning (manual calibration changes only)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum
from .trade_intent import DirectionalBias


@dataclass
class DecisionHistoryEntry:
    """
    Single historical decision record.
    Immutable snapshot of a past TradeIntent.
    
    Schema Version: 1.1.0
    """
    # Identity
    decision_id: str  # UUID for unique identification
    symbol: str
    analysis_timestamp: datetime
    
    # Core decision output
    directional_bias: DirectionalBias
    conviction_score: float  # 0-100
    
    # Quality metadata (for drift analysis)
    calibration_version: Optional[str] = None
    pillar_count_active: int = 0
    pillar_count_placeholder: int = 0
    pillar_count_failed: int = 0
    
    # Provenance
    engine_version: str = "1.0.0"  # QUAD engine version
    contract_version: str = "1.0.0"  # TradeIntent contract version
    
    # Lifecycle
    created_at: Optional[datetime] = None  # When record was stored
    is_superseded: bool = False  # True if newer analysis exists
    
    # Optional: Store full pillar breakdown for detailed analysis
    pillar_scores: Optional[Dict[str, float]] = None  # {"trend": 83.33, ...}
    pillar_biases: Optional[Dict[str, str]] = None  # {"trend": "BULLISH", ...}
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for storage."""
        return {
            "decision_id": self.decision_id,
            "symbol": self.symbol,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "directional_bias": self.directional_bias.value,
            "conviction_score": self.conviction_score,
            "calibration_version": self.calibration_version,
            "pillar_count_active": self.pillar_count_active,
            "pillar_count_placeholder": self.pillar_count_placeholder,
            "pillar_count_failed": self.pillar_count_failed,
            "engine_version": self.engine_version,
            "contract_version": self.contract_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_superseded": self.is_superseded,
            "pillar_scores": self.pillar_scores,
            "pillar_biases": self.pillar_biases,
        }
    
    @classmethod
    def from_trade_intent(cls, trade_intent, decision_id: str):
        """
        Create history entry from TradeIntent.
        
        Args:
            trade_intent: TradeIntent v1.0 or v1.1 object
            decision_id: Unique identifier for this decision
        
        Returns:
            DecisionHistoryEntry
        """
        # Extract pillar scores and biases
        pillar_scores = {}
        pillar_biases = {}
        for contrib in trade_intent.pillar_contributions:
            pillar_scores[contrib.name] = contrib.score
            pillar_biases[contrib.name] = contrib.bias
        
        # Extract calibration version (v1.1 field, optional)
        calibration_version = None
        if hasattr(trade_intent.quality, 'calibration_version'):
            calibration_version = trade_intent.quality.calibration_version
        
        return cls(
            decision_id=decision_id,
            symbol=trade_intent.symbol,
            analysis_timestamp=trade_intent.analysis_timestamp,
            directional_bias=trade_intent.directional_bias,
            conviction_score=trade_intent.conviction_score,
            calibration_version=calibration_version,
            pillar_count_active=trade_intent.quality.active_pillars,
            pillar_count_placeholder=trade_intent.quality.placeholder_pillars,
            pillar_count_failed=len(trade_intent.quality.failed_pillars),
            engine_version="1.1.0",
            contract_version=trade_intent.contract_version,
            created_at=datetime.now(),
            is_superseded=False,
            pillar_scores=pillar_scores,
            pillar_biases=pillar_biases,
        )


@dataclass
class DecisionHistory:
    """
    Collection of historical decisions for a symbol.
    
    CRITICAL CONSTRAINTS:
    - Read-only access (no decision mutation)
    - No execution logic (pure storage)
    - No predictive modeling (historical data only)
    - No auto-learning (manual calibration changes only)
    
    Schema Version: 1.1.0
    """
    symbol: str
    entries: List[DecisionHistoryEntry] = field(default_factory=list)
    
    # Metadata (computed from entries)
    earliest_decision: Optional[datetime] = None
    latest_decision: Optional[datetime] = None
    total_decisions: int = 0
    
    def __post_init__(self):
        """Compute metadata after initialization."""
        self._update_metadata()
    
    def _update_metadata(self):
        """Recompute metadata from entries."""
        if not self.entries:
            self.earliest_decision = None
            self.latest_decision = None
            self.total_decisions = 0
            return
        
        timestamps = [e.analysis_timestamp for e in self.entries]
        self.earliest_decision = min(timestamps)
        self.latest_decision = max(timestamps)
        self.total_decisions = len(self.entries)
    
    def add_entry(self, entry: DecisionHistoryEntry):
        """
        Add new decision entry.
        
        Args:
            entry: DecisionHistoryEntry to add
        """
        self.entries.append(entry)
        self._update_metadata()
    
    def get_recent(self, limit: int = 10) -> List[DecisionHistoryEntry]:
        """
        Return N most recent decisions.
        
        Args:
            limit: Maximum number of entries to return
        
        Returns:
            List of DecisionHistoryEntry, sorted by timestamp (newest first)
        """
        return sorted(
            self.entries,
            key=lambda x: x.analysis_timestamp,
            reverse=True
        )[:limit]
    
    def get_by_date_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[DecisionHistoryEntry]:
        """
        Filter decisions within date range.
        
        Args:
            start: Start datetime (inclusive)
            end: End datetime (inclusive)
        
        Returns:
            List of DecisionHistoryEntry within range
        """
        return [
            e for e in self.entries
            if start <= e.analysis_timestamp <= end
        ]
    
    def get_bias_distribution(self) -> Dict[str, int]:
        """
        Count occurrences of each bias (for observability).
        
        Returns:
            Dictionary mapping bias to count
            Example: {"BULLISH": 15, "BEARISH": 5, "NEUTRAL": 10}
        """
        from collections import Counter
        return dict(Counter(e.directional_bias.value for e in self.entries))
    
    def get_average_conviction(self) -> float:
        """
        Calculate mean conviction score across all entries.
        
        Returns:
            Average conviction score (0-100)
        """
        if not self.entries:
            return 0.0
        
        total = sum(e.conviction_score for e in self.entries)
        return round(total / len(self.entries), 2)
    
    def get_conviction_range(self) -> tuple:
        """
        Get min and max conviction scores.
        
        Returns:
            Tuple of (min_conviction, max_conviction)
        """
        if not self.entries:
            return (0.0, 0.0)
        
        scores = [e.conviction_score for e in self.entries]
        return (min(scores), max(scores))
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for API response."""
        return {
            "symbol": self.symbol,
            "entries": [e.to_dict() for e in self.entries],
            "earliest_decision": self.earliest_decision.isoformat() if self.earliest_decision else None,
            "latest_decision": self.latest_decision.isoformat() if self.latest_decision else None,
            "total_decisions": self.total_decisions,
        }
