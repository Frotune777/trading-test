from .base_pillar import BasePillar
from ...core.market_snapshot import LiveDecisionSnapshot, SessionContext
from ...core.config import settings
from typing import Tuple, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from ..pillar_config import PillarConfig

class MomentumPillar(BasePillar):
    """
    Analyzes momentum using RSI and MACD.
    Migrated from RecommendationService._calculate_technical_score.
    """
    
    def analyze(
        self, 
        snapshot: LiveDecisionSnapshot, 
        context: SessionContext,
        config: Optional['PillarConfig'] = None
    ) -> Tuple[float, str, dict, str]:
        """
        Analyze momentum using RSI and MACD.
        """
        score = 0.0
        explanation_parts = []
        
        # Resolve thresholds
        rsi_overbought = config.rsi_overbought if config and config.rsi_overbought else settings.MOMENTUM_RSI_OVERBOUGHT
        rsi_oversold = config.rsi_oversold if config and config.rsi_oversold else settings.MOMENTUM_RSI_OVERSOLD
        
        # Check if momentum indicators are available
        if snapshot.rsi is None:
            # No momentum data, return neutral
            return 50.0, "NEUTRAL", {}, "RSI data is not available for momentum analysis."
        
        # 1. RSI Scoring (20 points)
        rsi_score = 0
        rsi = snapshot.rsi
        
        # Note: logic simplification for readability could act as bounds check
        if settings.MOMENTUM_RSI_BULLISH_MIN < rsi < settings.MOMENTUM_RSI_BULLISH_MAX:
             rsi_score = 20  # Bullish momentum
             explanation_parts.append(f"RSI is {rsi:.2f}, indicating strong bullish momentum.")
        elif rsi >= rsi_overbought:
             rsi_score = 10  # Overbought (caution)
             explanation_parts.append(f"RSI is {rsi:.2f}, which is in the overbought territory. This suggests a potential for a pullback, but also confirms strong buying pressure.")
        elif rsi <= rsi_oversold:
             rsi_score = 10  # Oversold (bounce potential)
             explanation_parts.append(f"RSI is {rsi:.2f}, which is in the oversold territory. This suggests a potential for a bullish reversal.")
        elif settings.MOMENTUM_RSI_NEUTRAL_MIN <= rsi <= settings.MOMENTUM_RSI_NEUTRAL_MAX:
            rsi_score = 5   # Neutral-weak
            explanation_parts.append(f"RSI is {rsi:.2f}, indicating weak or neutral momentum.")
        else:
            explanation_parts.append(f"RSI is {rsi:.2f}, indicating bearish momentum.")

        # 2. MACD Scoring (20 points)
        macd_score = 0
        if snapshot.macd_hist is not None and snapshot.macd is not None and snapshot.macd_signal is not None:
            if snapshot.macd_hist > 0:
                macd_score += 10
                explanation_parts.append("The MACD histogram is positive, indicating that bullish momentum is increasing.")
            else:
                explanation_parts.append("The MACD histogram is negative, indicating that bearish momentum is increasing.")
            if snapshot.macd > snapshot.macd_signal:
                macd_score += 10
                explanation_parts.append("The MACD line is above the signal line, which is a bullish crossover signal.")
            else:
                explanation_parts.append("The MACD line is below the signal line, which is a bearish crossover signal.")
        else:
            explanation_parts.append("MACD data is not available.")

        # Total momentum score (max settings.MOMENTUM_SCORE_MAX)
        total_score = rsi_score + macd_score
        
        # Normalize to 0-100 scale
        # 40 points possible -> scale to 100
        normalized_score = (total_score / settings.MOMENTUM_SCORE_MAX) * 100.0
        
        # Determine bias based on RSI and MACD
        if rsi > settings.MOMENTUM_RSI_BIAS_BULLISH and snapshot.macd_hist and snapshot.macd_hist > 0:
            bias = "BULLISH"
        elif rsi < settings.MOMENTUM_RSI_BIAS_BEARISH and snapshot.macd_hist and snapshot.macd_hist < 0:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"
        
        metrics = {
            "RSI": round(snapshot.rsi, 2) if snapshot.rsi else "N/A",
            "MACD": round(snapshot.macd, 2) if snapshot.macd else "N/A",
            "MACD Hist": round(snapshot.macd_hist, 2) if snapshot.macd_hist else "N/A",
            "MACD Signal": round(snapshot.macd_signal, 2) if snapshot.macd_signal else "N/A"
        }
        
        explanation = " ".join(explanation_parts)

        return self._validate_score(normalized_score), bias, metrics, explanation
