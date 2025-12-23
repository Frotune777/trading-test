from .base_pillar import BasePillar
from ...core.market_snapshot import LiveDecisionSnapshot, SessionContext
from typing import Tuple

class SentimentPillar(BasePillar):
    """
    Analyzes derivatives sentiment using Greeks and OI changes.
    Wired to derivatives data in LiveDecisionSnapshot.
    """
    
    def analyze(self, snapshot: LiveDecisionSnapshot, context: SessionContext) -> Tuple[float, str]:
        """
        Analyze derivatives sentiment from snapshot.
        
        Key signals:
        - OI Change direction (buildup vs unwinding)
        - Delta exposure (directional bias)
        - Gamma risk (acceleration potential)
        """
        score = 50.0  # Neutral baseline
        bias = "NEUTRAL"
        
        # Check if derivatives data is available
        has_greeks = snapshot.delta is not None
        has_oi = snapshot.oi_change is not None
        
        if not has_greeks and not has_oi:
            # Return valid structure even if data missing
            return score, bias, {
                "OI Change": "N/A",
                "Delta": "N/A",
                "Gamma": "N/A"
            }
        
        # 1. OI Change Analysis (40 points)
        if has_oi and snapshot.oi_change:
            # Positive OI change suggests new positions
            if snapshot.oi_change > 0:
                # Price up + OI up = Long buildup (Bullish)
                if snapshot.ltp > snapshot.prev_close:
                    score += 20
                    bias = "BULLISH"
                # Price down + OI up = Short buildup (Bearish)
                else:
                    score -= 20
                    bias = "BEARISH"
            elif snapshot.oi_change < 0:
                # OI decreasing suggests unwinding
                if snapshot.ltp > snapshot.prev_close:
                    # Short covering (Mildly Bullish)
                    score += 10
                else:
                    # Long unwinding (Mildly Bearish)
                    score -= 10
        
        # 2. Delta Exposure (30 points)
        if has_greeks and snapshot.delta:
            # Delta > 0.5 suggests call-heavy (Bullish)
            # Delta < -0.5 suggests put-heavy (Bearish)
            if snapshot.delta > 0.5:
                score += 15
                bias = "BULLISH" if bias == "NEUTRAL" else bias
            elif snapshot.delta < -0.5:
                score -= 15
                bias = "BEARISH" if bias == "NEUTRAL" else bias
        
        # 3. Gamma Risk (10 points)
        if has_greeks and snapshot.gamma:
            # High gamma suggests large moves possible
            # Reduce confidence if gamma is very high
            if abs(snapshot.gamma) > 0.05:
                # High gamma = higher uncertainty
                # Pull score toward neutral
                score = score * 0.9 + 50 * 0.1
        
        metrics = {
            "OI Change": snapshot.oi_change if has_oi else "N/A",
            "Delta": round(snapshot.delta, 4) if has_greeks else "N/A",
            "Gamma": round(snapshot.gamma, 4) if has_greeks else "N/A"
        }

        return self._validate_score(score), bias, metrics
