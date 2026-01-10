from .base_pillar import BasePillar
from ...core.market_snapshot import LiveDecisionSnapshot, SessionContext
from ...core.exceptions import DataIncompleteError
from ...core.config import settings
from typing import Tuple, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from ..pillar_config import PillarConfig

class TrendPillar(BasePillar):
    """
    Analyzes price trend using moving averages.
    Migrated from RecommendationService._calculate_technical_score.
    """
    
    def analyze(
        self, 
        snapshot: LiveDecisionSnapshot, 
        context: SessionContext,
        config: Optional['PillarConfig'] = None
    ) -> Tuple[float, str, dict, str]:
        """
        Analyze trend using SMA alignment.
        """
        score = 0.0
        explanation_parts = []
        
        # Resolve thresholds
        sma_short_period = config.trend_sma_short if config and config.trend_sma_short else settings.TREND_SMA_DAILY_SHORT
        sma_long_period = config.trend_sma_long if config and config.trend_sma_long else settings.TREND_SMA_DAILY_LONG
        sma_weekly_period = settings.TREND_SMA_WEEKLY # No config override yet
        
        # Check if technical indicators are available
        if not snapshot.sma_50 or not snapshot.sma_200:
            raise DataIncompleteError(
                f"Missing trend indicators (SMA50/200) for {snapshot.symbol}",
                missing_fields=["sma_50", "sma_200"]
            )
        
        # 1. Daily Trend (30 points)
        daily_score = 0
        if snapshot.ltp > snapshot.sma_200:
            daily_score += 10
            explanation_parts.append(f"Price is above the {sma_long_period}-day SMA, which is a long-term bullish signal.")
        else:
            explanation_parts.append(f"Price is below the {sma_long_period}-day SMA, which is a long-term bearish signal.")

        if snapshot.sma_50 > snapshot.sma_200:
            daily_score += 10
            explanation_parts.append(f"The {sma_short_period}-day SMA is above the {sma_long_period}-day SMA (a 'golden cross'), which is a medium-term bullish signal.")
        else:
            explanation_parts.append(f"The {sma_short_period}-day SMA is below the {sma_long_period}-day SMA (a 'death cross'), which is a medium-term bearish signal.")

        if snapshot.ltp > snapshot.sma_50:
            daily_score += 10
            explanation_parts.append(f"Price is above the {sma_short_period}-day SMA, which is a short-term bullish signal.")
        else:
            explanation_parts.append(f"Price is below the {sma_short_period}-day SMA, which is a short-term bearish signal.")
        
        # 2. Weekly Trend Confirmation (30 points)
        weekly_score = 0
        if snapshot.sma_20_weekly:
            if snapshot.ltp > snapshot.sma_20_weekly:
                weekly_score = 30
                explanation_parts.append(f"Price is above the {sma_weekly_period}-week SMA, confirming the bullish trend on a longer timeframe.")
            else:
                explanation_parts.append(f"Price is below the {sma_weekly_period}-week SMA, confirming the bearish trend on a longer timeframe.")
        
        # Total trend score (max settings.TREND_SCORE_MAX)
        total_score = daily_score + weekly_score
        
        # Normalize to 0-100 scale
        normalized_score = (total_score / settings.TREND_SCORE_MAX) * 100.0
        
        # Determine bias
        if normalized_score > settings.TREND_BIAS_BULLISH:
            bias = "BULLISH"
        elif normalized_score < settings.TREND_BIAS_BEARISH:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"
        
        metrics = {
            "LTP": round(snapshot.ltp, 2),
            f"SMA {sma_short_period}": round(snapshot.sma_50, 2) if snapshot.sma_50 else "N/A",
            f"SMA {sma_long_period}": round(snapshot.sma_200, 2) if snapshot.sma_200 else "N/A",
            f"Weekly SMA {sma_weekly_period}": round(snapshot.sma_20_weekly, 2) if snapshot.sma_20_weekly else "N/A"
        }
        
        explanation = " ".join(explanation_parts)

        return self._validate_score(normalized_score), bias, metrics, explanation
