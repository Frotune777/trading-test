from .base_pillar import BasePillar
from ...core.market_snapshot import LiveDecisionSnapshot, SessionContext
from ...core.exceptions import DataIncompleteError
from typing import Tuple

class LiquidityPillar(BasePillar):
    """
    Analyzes market liquidity using bid-ask spreads, depth, and volume.
    Implements calibration matrix from pillar_calibration_matrices.md v1.0
    """
    
    def analyze(self, snapshot: LiveDecisionSnapshot, context: SessionContext) -> Tuple[float, str, dict, str]:
        """
        Analyze liquidity using calibrated thresholds.
        
        Returns:
            (score: float, bias: str, metrics: dict, explanation: str) where score ∈ [0,100]
        """
        explanation_parts = []
        
        # Track data availability
        has_spread = (snapshot.bid_price is not None and 
                     snapshot.ask_price is not None and
                     snapshot.spread_pct is not None)
        has_depth = (snapshot.bid_qty is not None and 
                    snapshot.ask_qty is not None and
                    snapshot.bid_qty > 0 and
                    snapshot.ask_qty > 0)
        has_adosc = snapshot.adosc is not None
        
        # Early return if no data (FAIL CLOSED logic)
        if not (has_spread or has_depth):
             raise DataIncompleteError(
                 f"Missing critical liquidity data for {snapshot.symbol}", 
                 missing_fields=["spread", "depth"]
             )
        
        # Component scores using calibration matrix
        spread_score = self._score_spread(snapshot.spread_pct, explanation_parts) if has_spread else None
        depth_score, depth_bias = self._score_depth(snapshot.bid_qty, snapshot.ask_qty, explanation_parts) if has_depth else (None, "NEUTRAL")
        
        # Base composite scoring
        if has_adosc:
            # With ADOSC formula
            weights = {'spread': 0.50, 'depth': 0.30, 'volume': 0.20}
            volume_score = 50.0  # Base volume score
            
            total_weight = 0.0
            weighted_score = 0.0
            
            if spread_score is not None:
                weighted_score += spread_score * weights['spread']
                total_weight += weights['spread']
            if depth_score is not None:
                weighted_score += depth_score * weights['depth']
                total_weight += weights['depth']
            
            # Volume component (always include if ADOSC present)
            weighted_score += volume_score * weights['volume']
            total_weight += weights['volume']
            
            base_score = weighted_score / total_weight if total_weight > 0 else 50.0
            
            # Apply ADOSC adjustment
            adosc_adjustment = self._score_adosc_adjustment(snapshot.adosc, explanation_parts)
            score = base_score + adosc_adjustment
        else:
            # Without ADOSC formula
            weights = {'spread': 0.60, 'depth': 0.40}
            total_weight = 0.0
            weighted_score = 0.0
            
            if spread_score is not None:
                weighted_score += spread_score * weights['spread']
                total_weight += weights['spread']
            if depth_score is not None:
                weighted_score += depth_score * weights['depth']
                total_weight += weights['depth']
            
            score = weighted_score / total_weight if total_weight > 0 else 50.0
        
        # Apply thin depth penalty (Calibration Rule)
        if has_depth:
            total_depth = snapshot.bid_qty + snapshot.ask_qty
            if total_depth < 100:
                score = 15.0  # Critically thin
                explanation_parts.append("Market depth is critically thin, indicating very high liquidity risk.")
            elif total_depth < 1000:
                score *= 0.6  # Thin depth penalty
                explanation_parts.append("Market depth is thin, increasing liquidity risk.")
        
        # Bias determination (Calibration Matrix Rules)
        bias = self._determine_bias(
            snapshot.spread_pct if has_spread else None,
            snapshot.bid_qty if has_depth else None,
            snapshot.ask_qty if has_depth else None,
            snapshot.adosc if has_adosc else None,
            depth_bias,
            explanation_parts
        )
        
        metrics = {
            "Spread %": round(snapshot.spread_pct, 4) if has_spread else "N/A",
            "Bid Qty": snapshot.bid_qty if has_depth else "N/A",
            "Ask Qty": snapshot.ask_qty if has_depth else "N/A",
            "Depth Ratio": round(snapshot.bid_qty / snapshot.ask_qty if has_depth and snapshot.ask_qty > 0 else 0, 2) if has_depth else "N/A",
             "ADOSC": round(snapshot.adosc, 2) if has_adosc else "N/A"
        }

        explanation = " ".join(explanation_parts)

        return self._validate_score(score), bias, metrics, explanation
    
    def _score_spread(self, spread_pct: float, explanation_parts: list) -> float:
        """
        Score bid-ask spread % using calibration matrix.
        """
        if spread_pct < 0.05:
            explanation_parts.append(f"The bid-ask spread is extremely tight ({spread_pct:.4f}%), indicating excellent liquidity.")
            return 95.0
        elif spread_pct < 0.10:
            explanation_parts.append(f"The bid-ask spread is very tight ({spread_pct:.4f}%), indicating very good liquidity.")
            return 85.0
        elif spread_pct < 0.20:
            explanation_parts.append(f"The bid-ask spread is tight ({spread_pct:.4f}%), indicating good liquidity.")
            return 70.0
        elif spread_pct < 0.30:
            explanation_parts.append(f"The bid-ask spread is fair ({spread_pct:.4f}%), indicating average liquidity.")
            return 50.0
        elif spread_pct < 0.50:
            explanation_parts.append(f"The bid-ask spread is wide ({spread_pct:.4f}%), indicating poor liquidity.")
            return 30.0
        else:  # >= 0.50
            explanation_parts.append(f"The bid-ask spread is very wide ({spread_pct:.4f}%), indicating very poor liquidity and high transaction costs.")
            return 10.0
    
    def _score_depth(self, bid_qty: int, ask_qty: int, explanation_parts: list) -> Tuple[float, str]:
        """
        Score market depth balance using calibration matrix.
        """
        depth_ratio = bid_qty / ask_qty if ask_qty > 0 else 0.0
        
        if depth_ratio < 0.5:
            explanation_parts.append(f"Market depth is heavily skewed towards sellers (ratio: {depth_ratio:.2f}), suggesting strong selling pressure.")
            return 60.0, "BEARISH"
        elif depth_ratio < 0.7:
            explanation_parts.append(f"Market depth is skewed towards sellers (ratio: {depth_ratio:.2f}), suggesting selling pressure.")
            return 70.0, "BEARISH"
        elif depth_ratio <= 1.3:
            explanation_parts.append(f"Market depth is balanced (ratio: {depth_ratio:.2f}), suggesting no immediate pressure in either direction.")
            return 80.0, "NEUTRAL"
        elif depth_ratio <= 2.0:
            explanation_parts.append(f"Market depth is skewed towards buyers (ratio: {depth_ratio:.2f}), suggesting buying pressure.")
            return 70.0, "BULLISH"
        else:  # > 2.0
            explanation_parts.append(f"Market depth is heavily skewed towards buyers (ratio: {depth_ratio:.2f}), suggesting strong buying pressure.")
            return 60.0, "BULLISH"
    
    def _score_adosc_adjustment(self, adosc: float, explanation_parts: list) -> float:
        """
        Calculate ADOSC adjustment using calibration matrix.
        """
        if adosc > 2000:
            explanation_parts.append(f"ADOSC is very high ({adosc:.2f}), indicating strong accumulation (buying).")
            return 15.0
        elif adosc > 1000:
            explanation_parts.append(f"ADOSC is high ({adosc:.2f}), indicating accumulation (buying).")
            return 10.0
        elif adosc > 0:
            explanation_parts.append(f"ADOSC is slightly positive ({adosc:.2f}), indicating weak accumulation.")
            return 5.0
        elif adosc > -1000:
            explanation_parts.append(f"ADOSC is slightly negative ({adosc:.2f}), indicating weak distribution (selling).")
            return -5.0
        elif adosc > -2000:
            explanation_parts.append(f"ADOSC is low ({adosc:.2f}), indicating distribution (selling).")
            return -10.0
        else:  # <= -2000
            explanation_parts.append(f"ADOSC is very low ({adosc:.2f}), indicating strong distribution (selling).")
            return -15.0
    
    def _determine_bias(self, spread_pct: float = None, bid_qty: int = None, 
                       ask_qty: int = None, adosc: float = None, depth_bias: str = "NEUTRAL", explanation_parts: list = None) -> str:
        """
        Determine directional bias using calibration rules.
        """
        # Rule 1: Poor liquidity conditions
        if spread_pct is not None and spread_pct > 0.30:
            if explanation_parts: explanation_parts.append("Wide spread is contributing to a 'BEARISH' bias due to poor liquidity.")
            return "BEARISH"
        
        if bid_qty is not None and ask_qty is not None:
            total_depth = bid_qty + ask_qty
            if total_depth < 1000:
                if explanation_parts: explanation_parts.append("Thin market depth is contributing to a 'BEARISH' bias due to high liquidity risk.")
                return "BEARISH"
            
            depth_ratio = bid_qty / ask_qty if ask_qty > 0 else 0.0
            
            # Rule 2: Strong buying interest
            if depth_ratio > 1.5 and adosc is not None and adosc > 1000:
                if explanation_parts: explanation_parts.append("High depth ratio and strong ADOSC are contributing to a 'BULLISH' bias.")
                return "BULLISH"
            
            # Rule 3: Strong selling pressure
            if depth_ratio < 0.7 and adosc is not None and adosc < -1000:
                if explanation_parts: explanation_parts.append("Low depth ratio and weak ADOSC are contributing to a 'BEARISH' bias.")
                return "BEARISH"
        
        # Rule 4: Default to depth-based bias or neutral
        if depth_bias != "NEUTRAL" and explanation_parts:
             explanation_parts.append(f"The depth bias of '{depth_bias}' is the primary driver of the overall liquidity bias.")

        return depth_bias if depth_bias != "NEUTRAL" else "NEUTRAL"
