from abc import ABC, abstractmethod
from typing import Tuple
from ...core.market_snapshot import LiveDecisionSnapshot, SessionContext

class BasePillar(ABC):
    """
    Abstract base for all QUAD analytical pillars.
    Each pillar must be stateless and deterministic.
    """
    
    @abstractmethod
    def analyze(
        self, 
        snapshot: LiveDecisionSnapshot, 
        context: SessionContext
    ) -> Tuple[float, str, dict]:
        """
        Analyze the snapshot and return a score.
        
        Returns:
            (score, bias, metrics) where:
                - score: float 0-100
                - bias: str "BULLISH" | "BEARISH" | "NEUTRAL"
                - metrics: dict of key indicators used
        """
        pass
    
    def _validate_score(self, score: float) -> float:
        """Ensure score is within bounds."""
        return max(0.0, min(100.0, score))
