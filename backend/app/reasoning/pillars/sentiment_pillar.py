from .base_pillar import BasePillar
from ...core.market_snapshot import LiveDecisionSnapshot, SessionContext
from ...core.config import settings
from typing import Tuple, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from ..pillar_config import PillarConfig

class SentimentPillar(BasePillar):
    """
    Analyzes derivatives sentiment using Greeks and OI changes.
    Wired to derivatives data in LiveDecisionSnapshot.
    """
    
    def analyze(
        self, 
        snapshot: LiveDecisionSnapshot, 
        context: SessionContext,
        config: Optional['PillarConfig'] = None
    ) -> Tuple[float, str, dict, str]:
        """
        Analyze derivatives sentiment from snapshot.
        
        Returns score, bias, metrics, and explanation.
        """
        score = 50.0  # Neutral baseline
        bias = "NEUTRAL"
        explanation_parts = []
        
        # Check if derivatives data is available
        has_greeks = snapshot.delta is not None
        has_oi = snapshot.oi_change is not None
        
        if not has_greeks and not has_oi:
            explanation_parts.append("No derivatives or OI data available.")
            pass
        
        # 1. OI Change Analysis (40 points)
        if has_oi and snapshot.oi_change:
            if snapshot.oi_change > 0:
                if snapshot.ltp > snapshot.prev_close:
                    score += settings.SENTIMENT_OI_BUILDUP_BONUS
                    bias = "BULLISH"
                    explanation_parts.append(f"Open interest increased while price went up, suggesting bullish long buildup.")
                else:
                    score -= settings.SENTIMENT_OI_BUILDUP_BONUS
                    bias = "BEARISH"
                    explanation_parts.append(f"Open interest increased while price went down, suggesting bearish short buildup.")
            elif snapshot.oi_change < 0:
                if snapshot.ltp > snapshot.prev_close:
                    score += settings.SENTIMENT_OI_COVERING_BONUS
                    explanation_parts.append(f"Open interest decreased while price went up, suggesting short covering, which is mildly bullish.")
                else:
                    score -= settings.SENTIMENT_OI_COVERING_BONUS
                    explanation_parts.append(f"Open interest decreased while price went down, suggesting long unwinding, which is mildly bearish.")
        
        # 2. Delta Exposure (30 points)
        if has_greeks and snapshot.delta:
            if snapshot.delta > settings.SENTIMENT_DELTA_THRESHOLD:
                score += settings.SENTIMENT_DELTA_BONUS
                bias = "BULLISH" if bias == "NEUTRAL" else bias
                explanation_parts.append(f"The option chain has a high positive delta ({snapshot.delta:.2f}), indicating a bullish bias from options traders.")
            elif snapshot.delta < -settings.SENTIMENT_DELTA_THRESHOLD:
                score -= settings.SENTIMENT_DELTA_BONUS
                bias = "BEARISH" if bias == "NEUTRAL" else bias
                explanation_parts.append(f"The option chain has a high negative delta ({snapshot.delta:.2f}), indicating a bearish bias from options traders.")
        
        # 3. Gamma Risk (10 points)
        if has_greeks and snapshot.gamma:
            if abs(snapshot.gamma) > settings.SENTIMENT_GAMMA_RISK_THRESHOLD:
                score = score * 0.9 + 50 * 0.1
                explanation_parts.append(f"Gamma is high ({snapshot.gamma:.4f}), which increases uncertainty and pulls the score towards neutral.")
        
        # 4. SENTNEL SIGNALS (NEW: Advanced Pattern Detection)
        sentinel_signals = []
        
        # A. Promoter Buyback Cluster (Aggressive Bullish)
        if snapshot.insider_buy_count and snapshot.insider_buy_count >= settings.SENTIMENT_INSIDER_BUY_COUNT_THRESHOLD:
            score += settings.SENTIMENT_INSIDER_CLUSTER_BONUS
            sentinel_signals.append("Promoter Buyback Cluster")
            bias = "BULLISH"
            explanation_parts.append(f"A cluster of {snapshot.insider_buy_count} insider buys detected, a strong bullish signal.")
        elif snapshot.insider_net_value and snapshot.insider_net_value > settings.SENTIMENT_INSIDER_NET_VALUE_THRESHOLD: # > 1 Cr
            score += settings.SENTIMENT_INSIDER_NET_VALUE_BONUS
            sentinel_signals.append("Significant Insider Buying")
            bias = "BULLISH" if bias == "NEUTRAL" else bias
            explanation_parts.append(f"Significant insider buying of ₹{snapshot.insider_net_value/1e7:.2f} Cr detected.")
            
        # B. Institutional Reverse (Bulk/Block Deals)
        total_deals = (snapshot.bulk_deal_net_qty or 0) + (snapshot.block_deal_net_qty or 0)
        if snapshot.volume and snapshot.volume > 0 and total_deals > (snapshot.volume * settings.SENTIMENT_INSTITUTIONAL_VOL_PCT): # Deals > 5% of day's volume
            score += settings.SENTIMENT_INSTITUTIONAL_BONUS
            sentinel_signals.append("Institutional Accumulation")
            bias = "BULLISH"
            explanation_parts.append("Significant institutional buying detected through bulk/block deals.")
        elif snapshot.volume and snapshot.volume > 0 and total_deals < -(snapshot.volume * settings.SENTIMENT_INSTITUTIONAL_VOL_PCT):
            score -= settings.SENTIMENT_INSTITUTIONAL_BONUS
            sentinel_signals.append("Institutional Distribution")
            bias = "BEARISH"
            explanation_parts.append("Significant institutional selling detected through bulk/block deals.")
            
        # C. Delivery-OI-Sentinel Divergence (The "Holy Grail" Setup)
        # High OI activity + Price holding + Sentinel buying
        if (snapshot.oi_change or 0) > 0 and snapshot.ltp >= snapshot.prev_close:
            if "Promoter Buyback Cluster" in sentinel_signals or "Institutional Accumulation" in sentinel_signals:
                score += settings.SENTIMENT_CONVERGENCE_BONUS # Stacked conviction
                sentinel_signals.append("SENTINEL-OI CONVERGENCE")
                explanation_parts.append("SENTINEL-OI CONVERGENCE detected: a powerful bullish signal combining OI buildup with institutional/insider buying.")

        metrics = {
            "OI Change": snapshot.oi_change if has_oi else "N/A",
            "Delta": round(snapshot.delta, 4) if has_greeks else "N/A",
            "Gamma": round(snapshot.gamma, 4) if has_greeks else "N/A",
            "Insider Buys": snapshot.insider_buy_count or 0,
            "Net Insider Value": f"₹{snapshot.insider_net_value/1e7:.2f}Cr" if snapshot.insider_net_value else "0",
            "Sentinel Signals": ", ".join(sentinel_signals) if sentinel_signals else "None"
        }
        
        explanation = " ".join(explanation_parts) if explanation_parts else "No specific sentiment signals detected."

        return self._validate_score(score), bias, metrics, explanation
