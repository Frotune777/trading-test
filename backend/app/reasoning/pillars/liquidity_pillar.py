from .base_pillar import BasePillar
from ...core.market_snapshot import LiveDecisionSnapshot, SessionContext
from typing import Tuple

class LiquidityPillar(BasePillar):
    """
    Analyzes market liquidity using bid-ask spreads, depth, and volume.
    Implements calibration matrix from pillar_calibration_matrices.md v1.0
    """
    
    def analyze(self, snapshot: LiveDecisionSnapshot, context: SessionContext) -> Tuple[float, str]:
        """
        Analyze liquidity using calibrated thresholds.
        
        Calibration Matrix (v1.0):
        - Spread%: <0.05 (95), 0.05-0.10 (85), 0.10-0.20 (70), 0.20-0.30 (50), 0.30-0.50 (30), >0.50 (10)
        - Depth Ratio: <0.5 (60,BEAR), 0.5-0.7 (70,BEAR), 0.7-1.3 (80,NEUT), 1.3-2.0 (70,BULL), >2.0 (60,BULL)
        - ADOSC: >2000 (+15,BULL), 1000-2000 (+10), 0-1000 (+5), -1000-0 (-5), -2000--1000 (-10,BEAR), <-2000 (-15,BEAR)
        
        Composite:
        - Without ADOSC: (Spread × 0.60) + (Depth × 0.40)
        - With ADOSC: (Spread × 0.50) + (Depth × 0.30) + (Volume × 0.20) + ADOSC_Adjustment
        
        Returns:
            (score: float, bias: str) where score ∈ [0,100]
        """
        # Track data availability
        has_spread = (snapshot.bid_price is not None and 
                     snapshot.ask_price is not None and
                     snapshot.spread_pct is not None)
        has_depth = (snapshot.bid_qty is not None and 
                    snapshot.ask_qty is not None and
                    snapshot.bid_qty > 0 and
                    snapshot.ask_qty > 0)
        has_adosc = snapshot.adosc is not None
        
        # Early return if no data
        if not (has_spread or has_depth):
            return 50.0, "NEUTRAL"
        
        # Component scores using calibration matrix
        spread_score = self._score_spread(snapshot.spread_pct) if has_spread else None
        depth_score, depth_bias = self._score_depth(snapshot.bid_qty, snapshot.ask_qty) if has_depth else (None, "NEUTRAL")
        
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
            adosc_adjustment = self._score_adosc_adjustment(snapshot.adosc)
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
            elif total_depth < 1000:
                score *= 0.6  # Thin depth penalty
        
        # Bias determination (Calibration Matrix Rules)
        bias = self._determine_bias(
            snapshot.spread_pct if has_spread else None,
            snapshot.bid_qty if has_depth else None,
            snapshot.ask_qty if has_depth else None,
            snapshot.adosc if has_adosc else None,
            depth_bias
        )
        
        return self._validate_score(score), bias
    
    def _score_spread(self, spread_pct: float) -> float:
        """
        Score bid-ask spread % using calibration matrix.
        
        Thresholds:
        - < 0.05%: 95 (Excellent)
        - 0.05-0.10%: 85 (Very Good)
        - 0.10-0.20%: 70 (Good)
        - 0.20-0.30%: 50 (Fair)
        - 0.30-0.50%: 30 (Poor)
        - > 0.50%: 10 (Very Poor)
        """
        if spread_pct < 0.05:
            return 95.0
        elif spread_pct < 0.10:
            return 85.0
        elif spread_pct < 0.20:
            return 70.0
        elif spread_pct < 0.30:
            return 50.0
        elif spread_pct < 0.50:
            return 30.0
        else:  # >= 0.50
            return 10.0
    
    def _score_depth(self, bid_qty: int, ask_qty: int) -> Tuple[float, str]:
        """
        Score market depth balance using calibration matrix.
        
        Returns: (score, bias)
        
        Thresholds (Depth Ratio = bid_qty ÷ ask_qty):
        - < 0.5: 60, BEARISH (Heavy Ask)
        - 0.5-0.7: 70, BEARISH (Ask Skewed)
        - 0.7-1.3: 80, NEUTRAL (Balanced)
        - 1.3-2.0: 70, BULLISH (Bid Skewed)
        - > 2.0: 60, BULLISH (Heavy Bid)
        """
        depth_ratio = bid_qty / ask_qty if ask_qty > 0 else 0.0
        
        if depth_ratio < 0.5:
            return 60.0, "BEARISH"
        elif depth_ratio < 0.7:
            return 70.0, "BEARISH"
        elif depth_ratio <= 1.3:
            return 80.0, "NEUTRAL"
        elif depth_ratio <= 2.0:
            return 70.0, "BULLISH"
        else:  # > 2.0
            return 60.0, "BULLISH"
    
    def _score_adosc_adjustment(self, adosc: float) -> float:
        """
        Calculate ADOSC adjustment using calibration matrix.
        
        Returns: adjustment value (can be negative)
        
        Thresholds:
        - > 2000: +15 (Strong Accumulation)
        - 1000-2000: +10 (Accumulation)
        - 0-1000: +5 (Weak Accumulation)
        - -1000-0: -5 (Weak Distribution)
        - -2000--1000: -10 (Distribution)
        - < -2000: -15 (Strong Distribution)
        """
        if adosc > 2000:
            return 15.0
        elif adosc > 1000:
            return 10.0
        elif adosc > 0:
            return 5.0
        elif adosc > -1000:
            return -5.0
        elif adosc > -2000:
            return -10.0
        else:  # <= -2000
            return -15.0
    
    def _determine_bias(self, spread_pct: float = None, bid_qty: int = None, 
                       ask_qty: int = None, adosc: float = None, depth_bias: str = "NEUTRAL") -> str:
        """
        Determine directional bias using calibration rules.
        
        Rules:
        1. If Spread > 0.30% OR Total_Depth < 1000 → "BEARISH" (Poor liquidity)
        2. Elif Depth_Ratio > 1.5 AND ADOSC > 1000 → "BULLISH" (Strong buying)
        3. Elif Depth_Ratio < 0.7 AND ADOSC < -1000 → "BEARISH" (Strong selling)
        4. Else → "NEUTRAL"
        """
        # Rule 1: Poor liquidity conditions
        if spread_pct is not None and spread_pct > 0.30:
            return "BEARISH"
        
        if bid_qty is not None and ask_qty is not None:
            total_depth = bid_qty + ask_qty
            if total_depth < 1000:
                return "BEARISH"
            
            depth_ratio = bid_qty / ask_qty if ask_qty > 0 else 0.0
            
            # Rule 2: Strong buying interest
            if depth_ratio > 1.5 and adosc is not None and adosc > 1000:
                return "BULLISH"
            
            # Rule 3: Strong selling pressure
            if depth_ratio < 0.7 and adosc is not None and adosc < -1000:
                return "BEARISH"
        
        # Rule 4: Default to depth-based bias or neutral
        return depth_bias if depth_bias != "NEUTRAL" else "NEUTRAL"
