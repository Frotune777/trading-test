# app/core/pillar_drift.py

"""
QUAD v1.1 - Pillar Drift Measurement Schema

Purpose: Quantify how individual pillar scores change between analyses.
Enables explainability of conviction changes.

CRITICAL CONSTRAINTS:
- Diagnostic only (no execution decisions)
- Descriptive metrics (no predictive modeling)
- No execution triggers based on drift thresholds
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Set, Optional, Tuple


@dataclass
class PillarScoreSnapshot:
    """
    Pillar scores at a specific point in time.
    
    Schema Version: 1.1.0
    """
    timestamp: datetime
    scores: Dict[str, float]  # {"trend": 83.33, "momentum": 65.0, ...}
    biases: Dict[str, str]    # {"trend": "BULLISH", "momentum": "BULLISH", ...}
    
    # Quality flags
    placeholder_pillars: Set[str] = field(default_factory=set)  # {"volatility", "liquidity"}
    failed_pillars: Set[str] = field(default_factory=set)       # Pillars that threw exceptions
    
    # Metadata
    calibration_version: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "scores": self.scores,
            "biases": self.biases,
            "placeholder_pillars": list(self.placeholder_pillars),
            "failed_pillars": list(self.failed_pillars),
            "calibration_version": self.calibration_version,
        }
    
    @classmethod
    def from_trade_intent(cls, trade_intent):
        """
        Create snapshot from TradeIntent.
        
        Args:
            trade_intent: TradeIntent v1.0 or v1.1 object
        
        Returns:
            PillarScoreSnapshot
        """
        scores = {}
        biases = {}
        placeholder_pillars = set()
        
        for contrib in trade_intent.pillar_contributions:
            scores[contrib.name] = contrib.score
            biases[contrib.name] = contrib.bias
            if contrib.is_placeholder:
                placeholder_pillars.add(contrib.name)
        
        # Extract calibration version (v1.1 field, optional)
        calibration_version = None
        if hasattr(trade_intent.quality, 'calibration_version'):
            calibration_version = trade_intent.quality.calibration_version
        
        return cls(
            timestamp=trade_intent.analysis_timestamp,
            scores=scores,
            biases=biases,
            placeholder_pillars=placeholder_pillars,
            failed_pillars=set(trade_intent.quality.failed_pillars),
            calibration_version=calibration_version,
        )


@dataclass
class PillarDriftMeasurement:
    """
    Comparison between two pillar snapshots.
    
    Purpose: Explain WHY conviction changed.
    NOT for execution decisions.
    
    Schema Version: 1.1.0
    """
    symbol: str
    previous_snapshot: PillarScoreSnapshot
    current_snapshot: PillarScoreSnapshot
    
    # Computed drift metrics (populated by compute_drift())
    score_deltas: Dict[str, float] = field(default_factory=dict)  # {"trend": +12.5, "momentum": -5.0, ...}
    bias_changes: Dict[str, Tuple[str, str]] = field(default_factory=dict)  # {"sentiment": ("NEUTRAL", "BULLISH"), ...}
    
    # Aggregated metrics
    max_drift_pillar: str = "none"
    max_drift_magnitude: float = 0.0
    total_drift_score: float = 0.0
    
    # Metadata
    time_delta_seconds: int = 0
    calibration_changed: bool = False
    
    def __post_init__(self):
        """Automatically compute drift on initialization."""
        self.compute_drift()
    
    def compute_drift(self) -> None:
        """
        Calculate drift metrics from snapshots.
        
        DETERMINISTIC: Same snapshots → Same drift metrics.
        """
        prev_scores = self.previous_snapshot.scores
        curr_scores = self.current_snapshot.scores
        
        # Score deltas
        self.score_deltas = {}
        for pillar in curr_scores:
            prev_score = prev_scores.get(pillar, 50.0)  # Default to neutral if missing
            curr_score = curr_scores[pillar]
            self.score_deltas[pillar] = round(curr_score - prev_score, 2)
        
        # Bias changes
        prev_biases = self.previous_snapshot.biases
        curr_biases = self.current_snapshot.biases
        
        self.bias_changes = {}
        for pillar in curr_biases:
            prev_bias = prev_biases.get(pillar, "NEUTRAL")
            curr_bias = curr_biases[pillar]
            if prev_bias != curr_bias:
                self.bias_changes[pillar] = (prev_bias, curr_bias)
        
        # Aggregated metrics
        abs_deltas = [abs(d) for d in self.score_deltas.values()]
        if abs_deltas:
            self.max_drift_magnitude = round(max(abs_deltas), 2)
            self.max_drift_pillar = max(
                self.score_deltas,
                key=lambda k: abs(self.score_deltas[k])
            )
            self.total_drift_score = round(sum(abs_deltas), 2)
        else:
            self.max_drift_magnitude = 0.0
            self.max_drift_pillar = "none"
            self.total_drift_score = 0.0
        
        # Time delta
        self.time_delta_seconds = int(
            (self.current_snapshot.timestamp - self.previous_snapshot.timestamp).total_seconds()
        )
        
        # Calibration check
        prev_cal = self.previous_snapshot.calibration_version
        curr_cal = self.current_snapshot.calibration_version
        self.calibration_changed = (
            prev_cal is not None and
            curr_cal is not None and
            prev_cal != curr_cal
        )
    
    def get_drift_classification(self) -> str:
        """
        Classify drift magnitude for UI display.
        
        Returns:
            str: "STABLE", "MODERATE", or "HIGH"
        """
        if self.total_drift_score < 10:
            return "STABLE"
        elif self.total_drift_score < 30:
            return "MODERATE"
        else:
            return "HIGH"
    
    def get_top_movers(self, limit: int = 3) -> list:
        """
        Get pillars with largest absolute score changes.
        
        Args:
            limit: Maximum number of pillars to return
        
        Returns:
            List of tuples: [(pillar_name, delta, prev_bias, curr_bias), ...]
        """
        # Sort by absolute delta
        sorted_pillars = sorted(
            self.score_deltas.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        top_movers = []
        for pillar, delta in sorted_pillars[:limit]:
            prev_bias = self.previous_snapshot.biases.get(pillar, "NEUTRAL")
            curr_bias = self.current_snapshot.biases.get(pillar, "NEUTRAL")
            top_movers.append((pillar, delta, prev_bias, curr_bias))
        
        return top_movers
    
    def get_drift_summary(self) -> str:
        """
        Generate human-readable drift summary.
        
        Returns:
            str: Narrative explanation of drift
        """
        classification = self.get_drift_classification()
        
        if classification == "STABLE":
            return f"Minimal drift detected ({self.total_drift_score:.1f} total points). Analysis is stable."
        
        top_movers = self.get_top_movers(limit=2)
        
        parts = [f"{classification} drift detected ({self.total_drift_score:.1f} total points)."]
        
        for pillar, delta, prev_bias, curr_bias in top_movers:
            direction = "increased" if delta > 0 else "decreased"
            parts.append(
                f"{pillar.capitalize()} {direction} by {abs(delta):.1f} points "
                f"({prev_bias} → {curr_bias})."
            )
        
        if self.calibration_changed:
            parts.append("⚠️ Calibration version changed.")
        
        return " ".join(parts)
    
    def to_dict(self) -> dict:
        """
        Serialize to dictionary for API response.
        
        Includes computed metrics and human-readable summary.
        """
        return {
            "symbol": self.symbol,
            "previous_snapshot": self.previous_snapshot.to_dict(),
            "current_snapshot": self.current_snapshot.to_dict(),
            "score_deltas": self.score_deltas,
            "bias_changes": {
                pillar: {"from": prev, "to": curr}
                for pillar, (prev, curr) in self.bias_changes.items()
            },
            "max_drift_pillar": self.max_drift_pillar,
            "max_drift_magnitude": self.max_drift_magnitude,
            "total_drift_score": self.total_drift_score,
            "time_delta_seconds": self.time_delta_seconds,
            "calibration_changed": self.calibration_changed,
            
            # Computed helpers
            "drift_classification": self.get_drift_classification(),
            "top_movers": [
                {
                    "pillar": pillar,
                    "delta": delta,
                    "previous_bias": prev_bias,
                    "current_bias": curr_bias,
                }
                for pillar, delta, prev_bias, curr_bias in self.get_top_movers()
            ],
            "drift_summary": self.get_drift_summary(),
        }
    
    @classmethod
    def from_trade_intents(
        cls,
        symbol: str,
        previous_intent,
        current_intent
    ):
        """
        Create drift measurement from two TradeIntent objects.
        
        Args:
            symbol: Symbol being analyzed
            previous_intent: Earlier TradeIntent
            current_intent: Later TradeIntent
        
        Returns:
            PillarDriftMeasurement
        """
        prev_snapshot = PillarScoreSnapshot.from_trade_intent(previous_intent)
        curr_snapshot = PillarScoreSnapshot.from_trade_intent(current_intent)
        
        return cls(
            symbol=symbol,
            previous_snapshot=prev_snapshot,
            current_snapshot=curr_snapshot,
        )
