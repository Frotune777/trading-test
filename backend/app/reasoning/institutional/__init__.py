"""
Institutional QUAD Core Types and Interfaces

This module defines the base types and interfaces for the institutional-grade
QUAD reasoning system. All pillars must implement these interfaces.

NO RETAIL INDICATORS ALLOWED.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import numpy as np


class PillarHealth(Enum):
    """Health status of a pillar."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class DirectionalBias(Enum):
    """Directional bias output from pillar analysis."""
    STRONG_BULLISH = "STRONG_BULLISH"
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    STRONG_BEARISH = "STRONG_BEARISH"


@dataclass
class PillarOutput:
    """
    Standardized output from any pillar.
    Replaces single score with probability distribution.
    
    This is the ONLY output format allowed from pillars.
    """
    pillar_name: str
    timestamp: datetime
    
    # Probability distribution (must sum to 1.0)
    prob_strong_bullish: float  # P(strong bullish)
    prob_bullish: float          # P(bullish)
    prob_neutral: float          # P(neutral)
    prob_bearish: float          # P(bearish)
    prob_strong_bearish: float   # P(strong bearish)
    
    # Most likely bias
    primary_bias: DirectionalBias
    
    # Confidence in primary bias (0-100)
    confidence: float
    
    # Health status
    health: PillarHealth
    health_message: Optional[str] = None
    
    # Feature contribution map (for auditability)
    feature_contributions: Dict[str, float] = field(default_factory=dict)
    
    # Data sources used (for traceability)
    data_sources: List[str] = field(default_factory=list)
    
    # Feature version
    feature_version: str = "1.0.0"
    
    # Risk flags
    risk_flags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate probability distribution."""
        total_prob = (
            self.prob_strong_bullish +
            self.prob_bullish +
            self.prob_neutral +
            self.prob_bearish +
            self.prob_strong_bearish
        )
        
        if not (0.99 <= total_prob <= 1.01):
            raise ValueError(
                f"Probabilities must sum to 1.0, got {total_prob:.4f}"
            )
    
    def expected_score(self) -> float:
        """
        Compute expected value of score (-100 to +100).
        Used for backward compatibility only.
        """
        return (
            self.prob_strong_bullish * 100 +
            self.prob_bullish * 50 +
            self.prob_neutral * 0 +
            self.prob_bearish * (-50) +
            self.prob_strong_bearish * (-100)
        )


class BasePillar:
    """
    Base class for all institutional pillars.
    
    All pillars MUST:
    1. Inherit from this class
    2. Implement analyze() method
    3. Implement check_health() method
    4. Use ONLY structural features (NO retail indicators)
    5. Return PillarOutput with probability distribution
    """
    
    def __init__(self, feature_version: str = "1.0.0"):
        self.feature_version = feature_version
        
    def analyze(self, input_bundle) -> PillarOutput:
        """
        Main analysis method.
        Must be implemented by each pillar.
        
        Args:
            input_bundle: Pillar-specific input data bundle
            
        Returns:
            PillarOutput with probability distribution
            
        Raises:
            NotImplementedError: If not overridden by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement analyze() method"
        )
        
    def check_health(self, input_bundle) -> tuple[PillarHealth, Optional[str]]:
        """
        Check if pillar has sufficient data to operate.
        
        Args:
            input_bundle: Pillar-specific input data bundle
            
        Returns:
            Tuple of (health_status, message)
            
        Raises:
            NotImplementedError: If not overridden by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement check_health() method"
        )
    
    def _score_to_logits(self, score: float) -> List[float]:
        """
        Convert continuous score to logits for 5 classes.
        
        Args:
            score: Continuous score in [-1, 1]
            
        Returns:
            List of 5 logits for [STRONG_BEARISH, BEARISH, NEUTRAL, BULLISH, STRONG_BULLISH]
        """
        # Score is in [-1, 1]
        # Map to logits for [STRONG_BEARISH, BEARISH, NEUTRAL, BULLISH, STRONG_BULLISH]
        
        if score > 0.5:  # Strong bullish
            return [-2, -1, 0, 1, 2 + (score - 0.5) * 4]
        elif score > 0:  # Bullish
            return [-2, -1, 0, 1 + score * 2, 1]
        elif score > -0.5:  # Bearish
            return [-1, -1 + abs(score) * 2, 0, -1, -2]
        else:  # Strong bearish
            return [-2 + (score + 0.5) * 4, -1, 0, -1, -2]
    
    def _softmax(self, logits: List[float]) -> List[float]:
        """
        Convert logits to probabilities using softmax.
        
        Args:
            logits: List of logit values
            
        Returns:
            List of probabilities (sum to 1.0)
        """
        exp_logits = [np.exp(x) for x in logits]
        sum_exp = sum(exp_logits)
        return [x / sum_exp for x in exp_logits]
    
    def _get_primary_bias(self, probs: List[float]) -> DirectionalBias:
        """
        Determine primary bias from probability distribution.
        
        Args:
            probs: List of 5 probabilities
            
        Returns:
            DirectionalBias enum value
        """
        max_idx = probs.index(max(probs))
        return [
            DirectionalBias.STRONG_BEARISH,
            DirectionalBias.BEARISH,
            DirectionalBias.NEUTRAL,
            DirectionalBias.BULLISH,
            DirectionalBias.STRONG_BULLISH
        ][max_idx]


class InsufficientDataError(Exception):
    """Raised when pillar cannot operate due to missing data."""
    pass
