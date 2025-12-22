from .base_pillar import BasePillar
from ...core.market_snapshot import LiveDecisionSnapshot, SessionContext
from typing import Tuple

class RegimePillar(BasePillar):
    """
    Analyzes market regime from SessionContext.
    Wired to MarketRegime service output.
    """
    
    def analyze(self, snapshot: LiveDecisionSnapshot, context: SessionContext) -> Tuple[float, str]:
        """
        Read market regime from context and map to score.
        
        Regime scoring:
        - BULLISH trending: 80-100
        - NEUTRAL/SIDEWAYS: 40-60
        - BEARISH trending: 0-20
        """
        regime = context.market_regime.upper()
        
        # Map regime string to score
        if regime == "BULLISH":
            score = 85.0
            bias = "BULLISH"
        elif regime == "BEARISH":
            score = 15.0
            bias = "BEARISH"
        elif regime in ["VOLATILE", "SIDEWAYS"]:
            score = 50.0
            bias = "NEUTRAL"
        else:  # UNKNOWN or other
            score = 50.0
            bias = "NEUTRAL"
        
        # Adjust based on VIX if available
        if context.vix_level:
            # High VIX reduces confidence in bullish regime
            if context.vix_level > 25 and regime == "BULLISH":
                score -= 10  # Reduce bullish confidence
            # Low VIX supports trending regimes
            elif context.vix_level < 15:
                if regime in ["BULLISH", "BEARISH"]:
                    score += 5  # Increase trend confidence
        
        return self._validate_score(score), bias
