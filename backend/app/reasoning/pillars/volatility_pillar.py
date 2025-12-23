from .base_pillar import BasePillar
from ...core.market_snapshot import LiveDecisionSnapshot, SessionContext
from typing import Tuple

class VolatilityPillar(BasePillar):
    """
    Analyzes price volatility using ATR, Bollinger Bands, and VIX.
    Implements calibration matrix from pillar_calibration_matrices.md v1.0
    """
    
    def analyze(self, snapshot: LiveDecisionSnapshot, context: SessionContext) -> Tuple[float, str]:
        """
        Analyze volatility using calibrated thresholds.
        
        Calibration Matrix (v1.0):
        - ATR% ranges: <1.5 (85), 1.5-3.0 (60), 3.0-5.0 (40), 5.0-8.0 (25), >8.0 (10)
        - BB Width%: <4 (80), 4-8 (60), 8-12 (40), 12-18 (25), >18 (15)
        - VIX: <12 (90), 12-15 (75), 15-20 (60), 20-25 (45), 25-30 (30), >30 (15)
        
        Composite: (ATR × 0.40) + (BB × 0.30) + (VIX × 0.30)
        
        Returns:
            (score: float, bias: str, metrics: dict) where score ∈ [0,100]
        """
        # Track data quality
        has_atr = snapshot.atr_pct is not None
        has_bb = snapshot.bb_width is not None
        has_vix = context.vix_level is not None and context.vix_level > 0
        
        # Early return if no data at all
        if not (has_atr or has_bb or has_vix):
            return 50.0, "NEUTRAL", {}
        
        # Component scores using calibration matrix
        atr_score = self._score_atr(snapshot.atr_pct) if has_atr else None
        bb_score = self._score_bb_width(snapshot.bb_width) if has_bb else None
        vix_score = self._score_vix(context.vix_level, context.vix_percentile) if has_vix else None
        
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
            context.vix_level if has_vix else None
        )
        
        metrics = {
            "ATR %": round(snapshot.atr_pct, 2) if has_atr else "N/A",
            "BB Width %": round(snapshot.bb_width, 2) if has_bb else "N/A",
            "India VIX": round(context.vix_level, 2) if has_vix else "N/A"
        }
        
        return self._validate_score(score), bias, metrics
    
    def _score_atr(self, atr_pct: float) -> float:
        """
        Score ATR% using calibration matrix thresholds.
        
        Thresholds:
        - < 1.5%: 85 (Very Low volatility)
        - 1.5-3.0%: 60 (Normal)
        - 3.0-5.0%: 40 (High)
        - 5.0-8.0%: 25 (Very High)
        - > 8.0%: 10 (Extreme)
        """
        if atr_pct < 1.5:
            return 85.0
        elif atr_pct < 3.0:
            return 60.0
        elif atr_pct < 5.0:
            return 40.0
        elif atr_pct < 8.0:
            return 25.0
        else:  # >= 8.0
            return 10.0
    
    def _score_bb_width(self, bb_width: float) -> float:
        """
        Score Bollinger Band Width % using calibration matrix.
        
        Thresholds:
        - < 4%: 80 (Narrow)
        - 4-8%: 60 (Normal)
        - 8-12%: 40 (Wide)
        - 12-18%: 25 (Very Wide)
        - > 18%: 15 (Extreme)
        """
        if bb_width < 4.0:
            return 80.0
        elif bb_width < 8.0:
            return 60.0
        elif bb_width < 12.0:
            return 40.0
        elif bb_width < 18.0:
            return 25.0
        else:  # >= 18.0
            return 15.0
    
    def _score_vix(self, vix_level: float, vix_percentile: float = None) -> float:
        """
        Score India VIX using calibration matrix.
        
        Thresholds:
        - < 12: 90 (Very Low)
        - 12-15: 75 (Low)
        - 15-20: 60 (Normal)
        - 20-25: 45 (Elevated)
        - 25-30: 30 (High)
        - > 30: 15 (Panic)
        
        Adjustments:
        - VIX < 10th percentile: -5 (complacency risk)
        """
        if vix_level < 12:
            base_score = 90.0
        elif vix_level < 15:
            base_score = 75.0
        elif vix_level < 20:
            base_score = 60.0
        elif vix_level < 25:
            base_score = 45.0
        elif vix_level < 30:
            base_score = 30.0
        else:  # >= 30
            base_score = 15.0
        
        # Apply percentile adjustment if available
        if vix_percentile is not None and vix_percentile < 10:
            base_score -= 5  # Complacency risk
        
        return base_score
    
    def _determine_bias(self, atr_pct: float = None, bb_width: float = None, vix: float = None) -> str:
        """
        Determine directional bias using calibration rules.
        
        Rule: ATR% >= 5.0 OR BB Width >= 12.0 OR VIX >= 25 → "VOLATILE"
        Otherwise → "NEUTRAL"
        """
        # Check volatility thresholds
        if atr_pct is not None and atr_pct >= 5.0:
            return "VOLATILE"
        if bb_width is not None and bb_width >= 12.0:
            return "VOLATILE"
        if vix is not None and vix >= 25:
            return "VOLATILE"
        
        return "NEUTRAL"
