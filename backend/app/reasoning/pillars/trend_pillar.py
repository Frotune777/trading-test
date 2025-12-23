from .base_pillar import BasePillar
from ...core.market_snapshot import LiveDecisionSnapshot, SessionContext
from typing import Tuple

class TrendPillar(BasePillar):
    """
    Analyzes price trend using moving averages.
    Migrated from RecommendationService._calculate_technical_score.
    """
    
    def analyze(self, snapshot: LiveDecisionSnapshot, context: SessionContext) -> Tuple[float, str]:
        """
        Analyze trend using SMA alignment.
        
        Scoring (60 points max, normalized to 100):
        - Price > SMA200: +10
        - SMA50 > SMA200: +10  
        - Price > SMA50: +10
        - Weekly SMA confirmation: +30
        
        Returns score 0-100 and bias and metrics.
        """
        score = 0.0
        
        # Check if technical indicators are available
        if not snapshot.sma_50 or not snapshot.sma_200:
            # No technical data, return neutral
            return 50.0, "NEUTRAL", {}
        
        # 1. Daily Trend (30 points)
        daily_score = 0
        if snapshot.ltp > snapshot.sma_200:
            daily_score += 10
        if snapshot.sma_50 > snapshot.sma_200:
            daily_score += 10
        if snapshot.ltp > snapshot.sma_50:
            daily_score += 10
        
        # 2. Weekly Trend Confirmation (30 points)
        weekly_score = 0
        if snapshot.sma_20_weekly:
            # Weekly close is proxied by current LTP for now
            # In a real implementation, we'd fetch actual weekly close
            if snapshot.ltp > snapshot.sma_20_weekly:
                weekly_score = 30
        
        # Total trend score (max 60)
        total_score = daily_score + weekly_score
        
        # Normalize to 0-100 scale
        # 60 points possible -> scale to 100
        normalized_score = (total_score / 60.0) * 100.0
        
        # Determine bias
        if normalized_score > 60:
            bias = "BULLISH"
        elif normalized_score < 40:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"
        
        metrics = {
            "LTP": round(snapshot.ltp, 2),
            "SMA 50": round(snapshot.sma_50, 2) if snapshot.sma_50 else "N/A",
            "SMA 200": round(snapshot.sma_200, 2) if snapshot.sma_200 else "N/A",
            "Weekly SMA": round(snapshot.sma_20_weekly, 2) if snapshot.sma_20_weekly else "N/A"
        }

        return self._validate_score(normalized_score), bias, metrics
