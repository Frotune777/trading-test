from .base_pillar import BasePillar
from ...core.market_snapshot import LiveDecisionSnapshot, SessionContext
from typing import Tuple

class MomentumPillar(BasePillar):
    """
    Analyzes momentum using RSI and MACD.
    Migrated from RecommendationService._calculate_technical_score.
    """
    
    def analyze(self, snapshot: LiveDecisionSnapshot, context: SessionContext) -> Tuple[float, str]:
        """
        Analyze momentum using RSI and MACD.
        
        Scoring (40 points max, normalized to 100):
        - RSI 50-70: +20 (Bullish momentum)
        - RSI >=70: +10 (Overbought caution)
        - RSI <=30: +10 (Oversold bounce potential)
        - RSI 40-50: +5 (Neutral-weak)
        - MACD Histogram > 0: +10
        - MACD > Signal: +10
        
        Returns score 0-100 and bias.
        """
        score = 0.0
        
        # Check if momentum indicators are available
        if snapshot.rsi is None:
            # No momentum data, return neutral
            return 50.0, "NEUTRAL"
        
        # 1. RSI Scoring (20 points)
        rsi_score = 0
        rsi = snapshot.rsi
        
        if 50 < rsi < 70:
            rsi_score = 20  # Bullish momentum
        elif rsi >= 70:
            rsi_score = 10  # Overbought (caution)
        elif rsi <= 30:
            rsi_score = 10  # Oversold (bounce potential)
        elif 40 <= rsi <= 50:
            rsi_score = 5   # Neutral-weak
        
        # 2. MACD Scoring (20 points)
        macd_score = 0
        if snapshot.macd_hist is not None and snapshot.macd is not None and snapshot.macd_signal is not None:
            if snapshot.macd_hist > 0:
                macd_score += 10
            if snapshot.macd > snapshot.macd_signal:
                macd_score += 10
        
        # Total momentum score (max 40)
        total_score = rsi_score + macd_score
        
        # Normalize to 0-100 scale
        # 40 points possible -> scale to 100
        normalized_score = (total_score / 40.0) * 100.0
        
        # Determine bias based on RSI and MACD
        if rsi > 55 and snapshot.macd_hist and snapshot.macd_hist > 0:
            bias = "BULLISH"
        elif rsi < 45 and snapshot.macd_hist and snapshot.macd_hist < 0:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"
        
        return self._validate_score(normalized_score), bias
