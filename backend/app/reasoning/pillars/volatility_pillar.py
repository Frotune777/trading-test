from .base_pillar import BasePillar
from ...core.market_snapshot import LiveDecisionSnapshot, SessionContext
from typing import Tuple

class VolatilityPillar(BasePillar):
    """
    Analyzes price volatility using ATR, Bollinger Bands, and VIX.
    Implements calibration matrix from pillar_calibration_matrices.md v1.0
    """
    
    def analyze(self, snapshot: LiveDecisionSnapshot, context: SessionContext) -> Tuple[float, str, dict, str]:
        """
        Analyze volatility using calibrated thresholds.
        
        Calibration Matrix (v1.0):
        - ATR% ranges: <1.5 (85), 1.5-3.0 (60), 3.0-5.0 (40), 5.0-8.0 (25), >8.0 (10)
        - BB Width%: <4 (80), 4-8 (60), 8-12 (40), 12-18 (25), >18 (15)
        - VIX: <12 (90), 12-15 (75), 15-20 (60), 20-25 (45), 25-30 (30), >30 (15)
        
        Composite: (ATR × 0.40) + (BB × 0.30) + (VIX × 0.30)
        
        Returns:
            (score: float, bias: str, metrics: dict, explanation: str) where score ∈ [0,100]
        """
        explanation_parts = []
        
        # Track data quality
        has_atr = snapshot.atr_pct is not None
        has_bb = snapshot.bb_width is not None
        has_vix = context.vix_level is not None and context.vix_level > 0
        
        # Early return if no data at all
        if not (has_atr or has_bb or has_vix):
            return 50.0, "NEUTRAL", {}, "No volatility data available."
        
        # Component scores using calibration matrix
        atr_score = self._score_atr(snapshot.atr_pct, explanation_parts) if has_atr else None
        bb_score = self._score_bb_width(snapshot.bb_width, explanation_parts) if has_bb else None
        vix_score = self._score_vix(context.vix_level, explanation_parts, context.vix_percentile) if has_vix else None
        
        # Composite scoring with dynamic weights
        weights = {'atr': 0.40, 'bb': 0.30, 'vix': 0.30}
        total_weight = 0.0
        weighted_score = 0.0
        
        if atr_score is not None:
            weighted_score += atr_score * weights['atr']
            total_weight += weights['atr']
        if bb_score is not None:
            weighted_score += bb_score * weights['bb']
            total_weight += weights['bb']
        if vix_score is not None:
            weighted_score += vix_score * weights['vix']
            total_weight += weights['vix']
        
        # Normalize if not all indicators available
        score = weighted_score / total_weight if total_weight > 0 else 50.0
        
        # Bias determination (Calibration Matrix Rule)
        bias = self._determine_bias(
            snapshot.atr_pct if has_atr else None,
            snapshot.bb_width if has_bb else None,
            context.vix_level if has_vix else None,
            explanation_parts
        )
        
        metrics = {
            "ATR %": round(snapshot.atr_pct, 2) if has_atr else "N/A",
            "BB Width %": round(snapshot.bb_width, 2) if has_bb else "N/A",
            "India VIX": round(context.vix_level, 2) if has_vix else "N/A"
        }
        
        explanation = " ".join(explanation_parts)
        
        return self._validate_score(score), bias, metrics, explanation
    
    def _score_atr(self, atr_pct: float, explanation_parts: list) -> float:
        """
        Score ATR% using calibration matrix thresholds.
        """
        if atr_pct < 1.5:
            explanation_parts.append(f"ATR is very low ({atr_pct:.2f}%), indicating low volatility.")
            return 85.0
        elif atr_pct < 3.0:
            explanation_parts.append(f"ATR is normal ({atr_pct:.2f}%), indicating moderate volatility.")
            return 60.0
        elif atr_pct < 5.0:
            explanation_parts.append(f"ATR is high ({atr_pct:.2f}%), indicating high volatility.")
            return 40.0
        elif atr_pct < 8.0:
            explanation_parts.append(f"ATR is very high ({atr_pct:.2f}%), indicating very high volatility.")
            return 25.0
        else:  # >= 8.0
            explanation_parts.append(f"ATR is extreme ({atr_pct:.2f}%), indicating extreme volatility.")
            return 10.0
    
    def _score_bb_width(self, bb_width: float, explanation_parts: list) -> float:
        """
        Score Bollinger Band Width % using calibration matrix.
        """
        if bb_width < 4.0:
            explanation_parts.append(f"Bollinger Bands are very narrow ({bb_width:.2f}%), suggesting a volatility squeeze is likely.")
            return 80.0
        elif bb_width < 8.0:
            explanation_parts.append(f"Bollinger Bands have a normal width ({bb_width:.2f}%), suggesting moderate volatility.")
            return 60.0
        elif bb_width < 12.0:
            explanation_parts.append(f"Bollinger Bands are wide ({bb_width:.2f}%), suggesting high volatility.")
            return 40.0
        elif bb_width < 18.0:
            explanation_parts.append(f"Bollinger Bands are very wide ({bb_width:.2f}%), suggesting very high volatility.")
            return 25.0
        else:  # >= 18.0
            explanation_parts.append(f"Bollinger Bands are extremely wide ({bb_width:.2f}%), suggesting extreme volatility.")
            return 15.0
    
    def _score_vix(self, vix_level: float, explanation_parts: list, vix_percentile: float = None) -> float:
        """
        Score India VIX using calibration matrix.
        """
        base_score = 0.0
        if vix_level < 12:
            base_score = 90.0
            explanation_parts.append(f"India VIX is very low ({vix_level:.2f}), indicating a calm market environment.")
        elif vix_level < 15:
            base_score = 75.0
            explanation_parts.append(f"India VIX is low ({vix_level:.2f}), indicating a calm market environment.")
        elif vix_level < 20:
            base_score = 60.0
            explanation_parts.append(f"India VIX is normal ({vix_level:.2f}), indicating a normal market environment.")
        elif vix_level < 25:
            base_score = 45.0
            explanation_parts.append(f"India VIX is elevated ({vix_level:.2f}), indicating a heightened level of market fear.")
        elif vix_level < 30:
            base_score = 30.0
            explanation_parts.append(f"India VIX is high ({vix_level:.2f}), indicating a high level of market fear.")
        else:  # >= 30
            base_score = 15.0
            explanation_parts.append(f"India VIX is very high ({vix_level:.2f}), indicating extreme market fear.")

        # Apply percentile adjustment if available
        if vix_percentile is not None and vix_percentile < 10:
            base_score -= 5  # Complacency risk
            explanation_parts.append(f"VIX is in the {vix_percentile:.0f}th percentile, which is very low and may indicate complacency risk.")
        
        return base_score
    
    def _determine_bias(self, atr_pct: float = None, bb_width: float = None, vix: float = None, explanation_parts: list = None) -> str:
        """
        Determine directional bias using calibration rules.
        """
        # Check volatility thresholds
        if atr_pct is not None and atr_pct >= 5.0:
            if explanation_parts: explanation_parts.append("High ATR is contributing to a 'VOLATILE' bias.")
            return "VOLATILE"
        if bb_width is not None and bb_width >= 12.0:
            if explanation_parts: explanation_parts.append("Wide Bollinger Bands are contributing to a 'VOLATILE' bias.")
            return "VOLATILE"
        if vix is not None and vix >= 25:
            if explanation_parts: explanation_parts.append("High VIX is contributing to a 'VOLATILE' bias.")
            return "VOLATILE"
        
        if explanation_parts: explanation_parts.append("Volatility metrics are within normal ranges, resulting in a 'NEUTRAL' bias.")
        return "NEUTRAL"
