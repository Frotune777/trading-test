"""
WeightScheduler Service
Dynamic pillar weight adjustment based on market regime and conditions.

This service maps market regimes to optimal pillar weight configurations,
allowing the QUAD reasoning engine to adapt to different market conditions.
"""

from typing import Dict, Optional
from app.core.config import settings


class WeightScheduler:
    """
    Maps MarketRegime to optimal pillar weight configurations.
    
    Weight matrices are designed to emphasize different pillars based on
    market conditions:
    - BULLISH: Trend and Momentum dominate
    - BEARISH: Trend and Volatility emphasized
    - VOLATILE: Volatility and Liquidity critical
    - SIDEWAYS: Sentiment and Regime more important
    """
    
    def __init__(self):
        """Initialize weight scheduler with configuration matrices."""
        self.enabled = settings.WEIGHT_SCHEDULER_ENABLED
        
        # Load weight matrices from config
        self.matrices = {
            "BULLISH": settings.WEIGHT_MATRIX_BULLISH,
            "BEARISH": settings.WEIGHT_MATRIX_BEARISH,
            "VOLATILE": settings.WEIGHT_MATRIX_VOLATILE,
            "SIDEWAYS": settings.WEIGHT_MATRIX_SIDEWAYS,
            "NEUTRAL": settings.WEIGHT_MATRIX_DEFAULT,
        }
        
        self.default_weights = settings.WEIGHT_MATRIX_DEFAULT
        self.vix_low = settings.WEIGHT_VIX_LOW_THRESHOLD
        self.vix_high = settings.WEIGHT_VIX_HIGH_THRESHOLD
        self.vix_adjustment = settings.WEIGHT_VIX_ADJUSTMENT_FACTOR
    
    def get_weights(
        self, 
        regime: str, 
        vix_level: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Returns optimized weights for current market conditions.
        
        Args:
            regime: Market regime (BULLISH, BEARISH, VOLATILE, SIDEWAYS, NEUTRAL)
            vix_level: Current VIX level for additional adjustments
            
        Returns:
            Dictionary of pillar weights (must sum to 1.0)
        """
        if not self.enabled:
            return self.default_weights.copy()
        
        # Get base weights for regime
        regime_upper = regime.upper() if regime else "NEUTRAL"
        weights = self.matrices.get(regime_upper, self.default_weights).copy()
        
        # Apply VIX-based adjustments if provided
        if vix_level is not None:
            weights = self._apply_vix_adjustment(weights, vix_level)
        
        # Ensure weights sum to 1.0 (normalize if needed)
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def _apply_vix_adjustment(
        self, 
        weights: Dict[str, float], 
        vix_level: float
    ) -> Dict[str, float]:
        """
        Adjusts weights based on VIX level.
        
        - Low VIX (<15): Reduce volatility weight, boost trend
        - High VIX (>25): Increase volatility weight, reduce trend
        """
        adjusted = weights.copy()
        
        if vix_level < self.vix_low:
            # Low volatility: reduce volatility pillar, boost trend
            adjustment = self.vix_adjustment
            adjusted["volatility"] = max(0.05, adjusted["volatility"] - adjustment)
            adjusted["trend"] = min(0.40, adjusted["trend"] + adjustment)
            
        elif vix_level > self.vix_high:
            # High volatility: increase volatility pillar, reduce trend
            adjustment = self.vix_adjustment
            adjusted["volatility"] = min(0.35, adjusted["volatility"] + adjustment)
            adjusted["trend"] = max(0.10, adjusted["trend"] - adjustment)
        
        return adjusted
    
    def should_rebalance(
        self, 
        current_regime: str, 
        prev_regime: Optional[str]
    ) -> bool:
        """
        Determines if weights need updating due to regime shift.
        
        Args:
            current_regime: Current market regime
            prev_regime: Previous market regime
            
        Returns:
            True if regime changed and rebalancing is needed
        """
        if not self.enabled or prev_regime is None:
            return False
        
        return current_regime.upper() != prev_regime.upper()
    
    def get_schedule_reason(self, regime: str, vix_level: Optional[float] = None) -> str:
        """
        Returns human-readable explanation for weight schedule.
        
        Args:
            regime: Market regime
            vix_level: Current VIX level
            
        Returns:
            Explanation string (e.g., "BULLISH_REGIME_LOW_VIX")
        """
        reason = regime.upper()
        
        if vix_level is not None:
            if vix_level < self.vix_low:
                reason += "_LOW_VIX"
            elif vix_level > self.vix_high:
                reason += "_HIGH_VIX"
        
        return reason
