# app/core/conviction_timeline.py

"""
QUAD v1.1 - Conviction Timeline Schema

Purpose: Track how conviction evolves over time for observability.
Enables signal stability analysis and drift detection.

CRITICAL CONSTRAINTS:
- Observability only (no execution triggers)
- Descriptive metrics (no predictive modeling)
- No auto-trading based on timeline patterns
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import statistics


@dataclass
class ConvictionDataPoint:
    """
    Single point in conviction timeline.
    
    Schema Version: 1.1.0
    """
    timestamp: datetime
    conviction_score: float  # 0-100
    directional_bias: str  # BULLISH/BEARISH/NEUTRAL/INVALID
    active_pillars: int  # How many pillars contributed
    
    # Context
    calibration_version: Optional[str] = None
    data_age_seconds: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "conviction_score": self.conviction_score,
            "directional_bias": self.directional_bias,
            "active_pillars": self.active_pillars,
            "calibration_version": self.calibration_version,
            "data_age_seconds": self.data_age_seconds,
        }


@dataclass
class ConvictionTimeline:
    """
    Time-series of conviction scores for a symbol.
    
    Purpose: Observability and drift detection.
    NOT for prediction or execution timing.
    
    Schema Version: 1.1.0
    """
    symbol: str
    data_points: List[ConvictionDataPoint] = field(default_factory=list)
    
    # Metadata (computed from data_points)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    sample_count: int = 0
    
    def __post_init__(self):
        """Compute metadata after initialization."""
        self._update_metadata()
    
    def _update_metadata(self):
        """Recompute metadata from data points."""
        if not self.data_points:
            self.start_time = None
            self.end_time = None
            self.sample_count = 0
            return
        
        timestamps = [dp.timestamp for dp in self.data_points]
        self.start_time = min(timestamps)
        self.end_time = max(timestamps)
        self.sample_count = len(self.data_points)
    
    def add_data_point(self, data_point: ConvictionDataPoint):
        """
        Add new data point to timeline.
        
        Args:
            data_point: ConvictionDataPoint to add
        """
        self.data_points.append(data_point)
        self._update_metadata()
    
    def get_conviction_volatility(self) -> float:
        """
        Calculate standard deviation of conviction scores.
        High volatility = unstable signal.
        
        Returns:
            float (0-100 scale, standard deviation)
        """
        if len(self.data_points) < 2:
            return 0.0
        
        scores = [dp.conviction_score for dp in self.data_points]
        return round(statistics.stdev(scores), 2)
    
    def get_bias_consistency(self) -> float:
        """
        Calculate percentage of time the bias remained unchanged.
        100% = perfectly stable bias.
        
        Returns:
            float (0-100 percentage)
        """
        if len(self.data_points) < 2:
            return 100.0
        
        # Count bias changes
        bias_changes = sum(
            1 for i in range(1, len(self.data_points))
            if self.data_points[i].directional_bias != self.data_points[i-1].directional_bias
        )
        
        # Calculate consistency percentage
        consistency = (1 - bias_changes / (len(self.data_points) - 1)) * 100
        return round(consistency, 2)
    
    def get_average_conviction(self) -> float:
        """
        Calculate mean conviction score over timeline.
        
        Returns:
            float (0-100 scale)
        """
        if not self.data_points:
            return 0.0
        
        total = sum(dp.conviction_score for dp in self.data_points)
        return round(total / len(self.data_points), 2)
    
    def get_conviction_trend(self) -> str:
        """
        Determine if conviction is trending up, down, or stable.
        
        Uses simple linear regression slope.
        
        Returns:
            str: "INCREASING", "DECREASING", or "STABLE"
        """
        if len(self.data_points) < 3:
            return "STABLE"
        
        # Simple linear regression
        n = len(self.data_points)
        x = list(range(n))  # Time index
        y = [dp.conviction_score for dp in self.data_points]
        
        # Calculate slope
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "STABLE"
        
        slope = numerator / denominator
        
        # Classify trend (threshold: ±1 point per sample)
        if slope > 1.0:
            return "INCREASING"
        elif slope < -1.0:
            return "DECREASING"
        else:
            return "STABLE"
    
    def get_recent_bias_streak(self) -> tuple:
        """
        Get current bias and how many consecutive times it appeared.
        
        Returns:
            Tuple of (bias: str, streak_count: int)
            Example: ("BULLISH", 5) means last 5 analyses were BULLISH
        """
        if not self.data_points:
            return ("NONE", 0)
        
        # Sort by timestamp (newest first)
        sorted_points = sorted(
            self.data_points,
            key=lambda x: x.timestamp,
            reverse=True
        )
        
        current_bias = sorted_points[0].directional_bias
        streak = 1
        
        for dp in sorted_points[1:]:
            if dp.directional_bias == current_bias:
                streak += 1
            else:
                break
        
        return (current_bias, streak)
    
    def get_conviction_percentiles(self) -> dict:
        """
        Calculate conviction score percentiles.
        
        Returns:
            Dictionary with p25, p50 (median), p75 percentiles
        """
        if not self.data_points:
            return {"p25": 0.0, "p50": 0.0, "p75": 0.0}
        
        scores = sorted([dp.conviction_score for dp in self.data_points])
        n = len(scores)
        
        return {
            "p25": scores[n // 4] if n >= 4 else scores[0],
            "p50": statistics.median(scores),
            "p75": scores[3 * n // 4] if n >= 4 else scores[-1],
        }
    
    def to_dict(self) -> dict:
        """
        Serialize to dictionary for API response.
        
        Includes computed metrics for frontend display.
        """
        bias, streak = self.get_recent_bias_streak()
        
        return {
            "symbol": self.symbol,
            "data_points": [dp.to_dict() for dp in self.data_points],
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "sample_count": self.sample_count,
            
            # Computed metrics
            "conviction_volatility": self.get_conviction_volatility(),
            "bias_consistency": self.get_bias_consistency(),
            "average_conviction": self.get_average_conviction(),
            "conviction_trend": self.get_conviction_trend(),
            "recent_bias": bias,
            "bias_streak_count": streak,
            "conviction_percentiles": self.get_conviction_percentiles(),
        }
    
    @classmethod
    def from_decision_history(cls, decision_history):
        """
        Build ConvictionTimeline from DecisionHistory.
        
        Args:
            decision_history: DecisionHistory object
        
        Returns:
            ConvictionTimeline
        """
        timeline = cls(symbol=decision_history.symbol)
        
        for entry in decision_history.entries:
            data_point = ConvictionDataPoint(
                timestamp=entry.analysis_timestamp,
                conviction_score=entry.conviction_score,
                directional_bias=entry.directional_bias.value,
                active_pillars=entry.pillar_count_active,
                calibration_version=entry.calibration_version,
                data_age_seconds=None,  # Not stored in history
            )
            timeline.add_data_point(data_point)
        
        return timeline
