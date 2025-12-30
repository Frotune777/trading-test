from .base_pillar import BasePillar
from ...core.market_snapshot import LiveDecisionSnapshot, SessionContext
from typing import Tuple

class RegimePillar(BasePillar):
    """
    Analyzes market regime from SessionContext.
    Wired to MarketRegime service output.
    """
    
    def analyze(self, snapshot: LiveDecisionSnapshot, context: SessionContext) -> Tuple[float, str, dict, str]:
        """
        Read market regime from context and map to score.
        
        Regime scoring:
        - BULLISH trending: 80-100
        - NEUTRAL/SIDEWAYS: 40-60
        - BEARISH trending: 0-20
        """
        regime = context.market_regime.upper()
        explanation_parts = []
        
        # Map regime string to score
        if regime == "BULLISH":
            score = 85.0
            bias = "BULLISH"
            explanation_parts.append(f"The market is in a '{regime}' regime, which is favorable for long positions.")
        elif regime == "BEARISH":
            score = 15.0
            bias = "BEARISH"
            explanation_parts.append(f"The market is in a '{regime}' regime, which is favorable for short positions.")
        elif regime in ["VOLATILE", "SIDEWAYS"]:
            score = 50.0
            bias = "NEUTRAL"
            explanation_parts.append(f"The market is in a '{regime}' regime, suggesting a lack of a clear trend.")
        else:  # UNKNOWN or other
            score = 50.0
            bias = "NEUTRAL"
            explanation_parts.append(f"The market regime is '{regime}', which is treated as neutral.")
        
        # Adjust based on VIX if available
        if context.vix_level:
            # High VIX reduces confidence in bullish regime
            if context.vix_level > 25 and regime == "BULLISH":
                score -= 10  # Reduce bullish confidence
                explanation_parts.append(f"However, the high VIX level ({context.vix_level:.2f}) suggests increased fear and reduces confidence in the bullish regime.")
            # Low VIX supports trending regimes
            elif context.vix_level < 15:
                if regime in ["BULLISH", "BEARISH"]:
                    score += 5  # Increase trend confidence
                    explanation_parts.append(f"The low VIX level ({context.vix_level:.2f}) indicates low market fear, which supports the current '{regime}' trend.")
        
        metrics = {
            "Regime": regime,
            "Market VIX": round(context.vix_level, 2) if context.vix_level else "N/A"
        }

        explanation = " ".join(explanation_parts)

        return self._validate_score(score), bias, metrics, explanation
