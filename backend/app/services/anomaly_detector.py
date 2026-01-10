"""
AnomalyDetector Service
Proactive detection of unusual pillar behavior or score patterns.

This service monitors pillar scores for anomalies that may indicate
data issues or unusual market conditions.
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from app.core.trade_intent import TradeIntent, PillarContribution

logger = logging.getLogger(__name__)


@dataclass
class Anomaly:
    """Detected anomaly in pillar behavior."""
    type: str  # "SUDDEN_DROP", "STUCK_PILLAR", "DIVERGENT_PILLARS", "EXTREME_VOLATILITY"
    pillar: str  # Affected pillar name (or "ALL" for system-wide)
    severity: str  # "LOW", "MEDIUM", "HIGH"
    description: str  # Human-readable explanation
    detected_at: datetime
    metric_value: Optional[float] = None  # The anomalous value


class AnomalyDetector:
    """
    Monitors pillar scores for unusual patterns.
    Uses sliding window of recent decisions for comparison.
    """
    
    # Detection thresholds
    SUDDEN_DROP_THRESHOLD = 30.0  # Score drop >30 points
    STUCK_PILLAR_COUNT = 10  # Same score for 10+ consecutive analyses
    DIVERGENT_PILLAR_THRESHOLD = 5  # 5+ pillars with opposite biases
    EXTREME_VOLATILITY_THRESHOLD = 25.0  # Score std_dev >25 over window
    
    # Time windows
    SUDDEN_DROP_WINDOW_MINUTES = 5
    VOLATILITY_WINDOW_MINUTES = 60
    
    def __init__(self, history_size: int = 50):
        """
        Initialize anomaly detector.
        
        Args:
            history_size: Number of recent decisions to keep in memory
        """
        self.history: List[TradeIntent] = []
        self.history_size = history_size
        self.pillar_score_history = {}  # pillar_name -> [scores]
    
    def detect_anomalies(
        self, 
        intent: TradeIntent, 
        symbol: str
    ) -> List[Anomaly]:
        """
        Detects anomalies in current intent compared to history.
        
        Args:
            intent: Current trade intent to analyze
            symbol: Symbol being analyzed
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Update history
        self._update_history(intent)
        
        # Run detection rules
        anomalies.extend(self._detect_sudden_drops(intent))
        anomalies.extend(self._detect_stuck_pillars(intent))
        anomalies.extend(self._detect_divergent_pillars(intent))
        anomalies.extend(self._detect_extreme_volatility(intent))
        
        if anomalies:
            logger.warning(f"Detected {len(anomalies)} anomalies for {symbol}")
        
        return anomalies
    
    def _update_history(self, intent: TradeIntent):
        """Updates internal history with new intent."""
        self.history.append(intent)
        
        # Maintain history size
        if len(self.history) > self.history_size:
            self.history.pop(0)
        
        # Update pillar score history
        for contrib in intent.pillar_contributions:
            if contrib.name not in self.pillar_score_history:
                self.pillar_score_history[contrib.name] = []
            
            self.pillar_score_history[contrib.name].append(contrib.score)
            
            # Maintain history size per pillar
            if len(self.pillar_score_history[contrib.name]) > self.history_size:
                self.pillar_score_history[contrib.name].pop(0)
    
    def _detect_sudden_drops(self, intent: TradeIntent) -> List[Anomaly]:
        """Detects sudden score drops (>30 points in <5 minutes)."""
        anomalies = []
        
        if len(self.history) < 2:
            return anomalies
        
        # Get recent history within time window
        cutoff_time = intent.analysis_timestamp - timedelta(minutes=self.SUDDEN_DROP_WINDOW_MINUTES)
        recent_intents = [h for h in self.history if h.analysis_timestamp >= cutoff_time]
        
        if len(recent_intents) < 2:
            return anomalies
        
        # Check each pillar for sudden drops
        for contrib in intent.pillar_contributions:
            pillar_name = contrib.name
            current_score = contrib.score
            
            # Find previous score for this pillar
            for prev_intent in reversed(recent_intents[:-1]):
                prev_contrib = next((c for c in prev_intent.pillar_contributions if c.name == pillar_name), None)
                if prev_contrib:
                    score_drop = prev_contrib.score - current_score
                    
                    if score_drop > self.SUDDEN_DROP_THRESHOLD:
                        anomalies.append(Anomaly(
                            type="SUDDEN_DROP",
                            pillar=pillar_name,
                            severity="HIGH",
                            description=f"{pillar_name.capitalize()} pillar dropped {score_drop:.1f} points in <{self.SUDDEN_DROP_WINDOW_MINUTES} minutes",
                            detected_at=intent.analysis_timestamp,
                            metric_value=score_drop
                        ))
                    break
        
        return anomalies
    
    def _detect_stuck_pillars(self, intent: TradeIntent) -> List[Anomaly]:
        """Detects pillars returning same score repeatedly."""
        anomalies = []
        
        for contrib in intent.pillar_contributions:
            pillar_name = contrib.name
            
            if pillar_name not in self.pillar_score_history:
                continue
            
            scores = self.pillar_score_history[pillar_name]
            
            # Check if last N scores are identical
            if len(scores) >= self.STUCK_PILLAR_COUNT:
                last_n_scores = scores[-self.STUCK_PILLAR_COUNT:]
                
                if len(set(last_n_scores)) == 1:  # All identical
                    anomalies.append(Anomaly(
                        type="STUCK_PILLAR",
                        pillar=pillar_name,
                        severity="MEDIUM",
                        description=f"{pillar_name.capitalize()} pillar stuck at {last_n_scores[0]:.1f} for {self.STUCK_PILLAR_COUNT}+ analyses",
                        detected_at=intent.analysis_timestamp,
                        metric_value=last_n_scores[0]
                    ))
        
        return anomalies
    
    def _detect_divergent_pillars(self, intent: TradeIntent) -> List[Anomaly]:
        """Detects high conflict between pillar biases."""
        anomalies = []
        
        # Count biases
        bullish_count = sum(1 for c in intent.pillar_contributions if c.bias == "BULLISH")
        bearish_count = sum(1 for c in intent.pillar_contributions if c.bias == "BEARISH")
        
        # High divergence if 5+ pillars disagree
        if bullish_count >= self.DIVERGENT_PILLAR_THRESHOLD and bearish_count >= self.DIVERGENT_PILLAR_THRESHOLD:
            anomalies.append(Anomaly(
                type="DIVERGENT_PILLARS",
                pillar="ALL",
                severity="MEDIUM",
                description=f"High pillar divergence: {bullish_count} BULLISH vs {bearish_count} BEARISH",
                detected_at=intent.analysis_timestamp,
                metric_value=abs(bullish_count - bearish_count)
            ))
        
        return anomalies
    
    def _detect_extreme_volatility(self, intent: TradeIntent) -> List[Anomaly]:
        """Detects extreme score variance over time window."""
        anomalies = []
        
        # Get recent history within time window
        cutoff_time = intent.analysis_timestamp - timedelta(minutes=self.VOLATILITY_WINDOW_MINUTES)
        recent_intents = [h for h in self.history if h.analysis_timestamp >= cutoff_time]
        
        if len(recent_intents) < 5:  # Need at least 5 data points
            return anomalies
        
        # Check each pillar for extreme volatility
        for contrib in intent.pillar_contributions:
            pillar_name = contrib.name
            
            # Collect scores for this pillar from recent history
            pillar_scores = []
            for hist_intent in recent_intents:
                hist_contrib = next((c for c in hist_intent.pillar_contributions if c.name == pillar_name), None)
                if hist_contrib:
                    pillar_scores.append(hist_contrib.score)
            
            if len(pillar_scores) >= 5:
                # Calculate variance
                mean_score = sum(pillar_scores) / len(pillar_scores)
                variance = sum((s - mean_score) ** 2 for s in pillar_scores) / len(pillar_scores)
                std_dev = variance ** 0.5
                
                if std_dev > self.EXTREME_VOLATILITY_THRESHOLD:
                    anomalies.append(Anomaly(
                        type="EXTREME_VOLATILITY",
                        pillar=pillar_name,
                        severity="LOW",
                        description=f"{pillar_name.capitalize()} pillar showing extreme volatility (σ={std_dev:.1f}) over {self.VOLATILITY_WINDOW_MINUTES}min",
                        detected_at=intent.analysis_timestamp,
                        metric_value=std_dev
                    ))
        
        return anomalies
    
    def clear_history(self):
        """Clears detection history (useful for testing or symbol changes)."""
        self.history.clear()
        self.pillar_score_history.clear()
