"""
PILLAR 4: Risk & Regime Context

Quantitative regime detection using volatility, correlation, and liquidity metrics.

Ownership:
- Volatility regime (percentile-based, NO hardcoded strings)
- Correlation regime (risk-on vs risk-off)
- Liquidity regime (market breadth)

NO OVERLAP with price structure, derivatives, or execution logic.
"""

import logging
from typing import Dict
import numpy as np
import pandas as pd
from datetime import datetime

from ..input_bundles import RegimeInput
from .. import BasePillar, PillarOutput, PillarHealth, DirectionalBias

logger = logging.getLogger(__name__)


class RegimePillar(BasePillar):
    """
    Quantitative regime detection.
    NO hardcoded regime strings - all derived from data.
    """
    
    def __init__(self, feature_version: str = "1.0.0"):
        super().__init__(feature_version)
        logger.info(f"Initialized RegimePillar v{feature_version}")
    
    def check_health(self, input_bundle: RegimeInput) -> tuple[PillarHealth, str]:
        """Check if sufficient regime data is available."""
        if input_bundle.vix_daily is None or len(input_bundle.vix_daily) < 60:
            return PillarHealth.FAILED, "Insufficient VIX data (need 60+ days)"
        
        if input_bundle.nifty_50_daily is None or len(input_bundle.nifty_50_daily) < 60:
            return PillarHealth.FAILED, "Insufficient index data"
        
        if input_bundle.symbol_daily is None or len(input_bundle.symbol_daily) < 60:
            return PillarHealth.FAILED, "Insufficient symbol price history"
        
        if input_bundle.market_breadth_30d is None or len(input_bundle.market_breadth_30d) < 10:
            return PillarHealth.DEGRADED, "Limited market breadth data"
        
        return PillarHealth.HEALTHY, None
    
    def analyze(self, input_bundle: RegimeInput) -> PillarOutput:
        """Derive regime from structural market characteristics."""
        health, health_msg = self.check_health(input_bundle)
        
        if health == PillarHealth.FAILED:
            return self._create_failed_output(input_bundle.symbol, health_msg)
        
        # 1. VOLATILITY REGIME (percentile-based)
        vol_regime = self._compute_volatility_regime(input_bundle.vix_daily)
        
        # 2. CORRELATION REGIME (risk-on vs risk-off)
        corr_regime = self._compute_correlation_regime(
            input_bundle.symbol_daily,
            input_bundle.nifty_50_daily
        )
        
        # 3. LIQUIDITY REGIME (market breadth)
        liquidity_regime = self._compute_liquidity_regime(
            input_bundle.market_breadth_30d
        )
        
        # 4. SECTOR ALIGNMENT
        sector_alignment = self._compute_sector_alignment(
            input_bundle.symbol_daily,
            input_bundle.sector_index_daily
        )
        
        features = {
            'volatility_regime': vol_regime['percentile'],
            'vol_expansion': vol_regime['expansion'],
            'correlation_regime': corr_regime['correlation'],
            'correlation_stability': corr_regime['stability'],
            'liquidity_regime': liquidity_regime['breadth'],
            'liquidity_deterioration': liquidity_regime['deterioration'],
            'sector_alignment': sector_alignment
        }
        
        return self._features_to_distribution(
            input_bundle.symbol,
            features,
            health,
            health_msg,
            input_bundle
        )
    
    def _compute_volatility_regime(self, vix_daily: pd.DataFrame) -> Dict:
        """
        Classify volatility regime using percentile ranking.
        
        Low vol (VIX < 20th percentile) = bullish for risk assets
        High vol (VIX > 80th percentile) = bearish
        """
        current_vix = vix_daily.iloc[-1]['close']
        
        # Compute percentile rank over last 252 days
        vix_values = vix_daily.tail(252)['close']
        percentile = (vix_values < current_vix).sum() / len(vix_values)
        
        # Vol expansion (recent vs historical)
        recent_vix = vix_values.tail(5).mean()
        hist_vix = vix_values.mean()
        expansion = (recent_vix - hist_vix) / hist_vix if hist_vix > 0 else 0.0
        
        # Invert percentile: low percentile (low VIX) = bullish
        # Map [0, 1] to [1, -1]
        regime_score = 1.0 - 2.0 * percentile
        
        return {
            'percentile': regime_score,
            'expansion': np.clip(expansion, -1.0, 1.0)
        }
    
    def _compute_correlation_regime(self,
                                      symbol_daily: pd.DataFrame,
                                      nifty_daily: pd.DataFrame) -> Dict:
        """
        Analyze correlation regime.
        
        High correlation = risk-on (bullish for beta)
        Low correlation = stock-specific (neutral)
        """
        # Compute rolling 60-day correlation
        symbol_returns = symbol_daily['close'].pct_change().tail(60)
        nifty_returns = nifty_daily['close'].pct_change().tail(60)
        
        correlation = symbol_returns.corr(nifty_returns)
        
        # Stability: how stable is correlation over time?
        if len(symbol_daily) >= 120:
            prev_60_symbol = symbol_daily['close'].pct_change().iloc[-120:-60]
            prev_60_nifty = nifty_daily['close'].pct_change().iloc[-120:-60]
            prev_corr = prev_60_symbol.corr(prev_60_nifty)
            
            stability = 1.0 - abs(correlation - prev_corr)
        else:
            stability = 0.5
        
        return {
            'correlation': correlation if not pd.isna(correlation) else 0.0,
            'stability': stability
        }
    
    def _compute_liquidity_regime(self, breadth_df: pd.DataFrame) -> Dict:
        """
        Analyze market breadth for liquidity regime.
        
        Broad participation (high advance/decline) = bullish
        Narrow leadership = bearish
        """
        if breadth_df.empty:
            return {'breadth': 0.0, 'deterioration': 0.0}
        
        # Average advance/decline ratio
        avg_ad_ratio = breadth_df['advance_decline_ratio'].tail(20).mean()
        
        # Deterioration: is breadth worsening?
        if len(breadth_df) >= 20:
            recent_ad = breadth_df['advance_decline_ratio'].tail(5).mean()
            prev_ad = breadth_df['advance_decline_ratio'].iloc[-20:-5].mean()
            deterioration = (prev_ad - recent_ad) / prev_ad if prev_ad > 0 else 0.0
        else:
            deterioration = 0.0
        
        # Normalize: 1.0 = neutral, 2.0 = strong breadth
        normalized = (avg_ad_ratio - 1.0)
        
        return {
            'breadth': np.clip(normalized, -1.0, 1.0),
            'deterioration': np.clip(deterioration, 0.0, 1.0)
        }
    
    def _compute_sector_alignment(self,
                                    symbol_daily: pd.DataFrame,
                                    sector_daily: pd.DataFrame) -> float:
        """
        Measure alignment with sector performance.
        
        Outperforming sector = bullish
        Underperforming = bearish
        """
        if sector_daily is None or sector_daily.empty:
            return 0.0
        
        # Compute 30-day returns
        symbol_ret = (symbol_daily['close'].iloc[-1] / symbol_daily['close'].iloc[-30] - 1)
        sector_ret = (sector_daily['close'].iloc[-1] / sector_daily['close'].iloc[-30] - 1)
        
        # Relative performance
        relative_perf = symbol_ret - sector_ret
        
        # Normalize: ±10% relative performance = ±1.0
        normalized = relative_perf / 0.10
        return np.clip(normalized, -1.0, 1.0)
    
    def _features_to_distribution(self,
                                    symbol: str,
                                    features: Dict[str, float],
                                    health: PillarHealth,
                                    health_msg: str,
                                    input_bundle: RegimeInput) -> PillarOutput:
        """Convert regime features to probability distribution."""
        # Regime pillar provides CONTEXT, not directional bias
        # Weight volatility regime heavily
        weights = {
            'volatility_regime': 0.40,
            'correlation_regime': 0.25,
            'liquidity_regime': 0.20,
            'sector_alignment': 0.15
        }
        
        weighted_score = sum(
            features.get(k, 0.0) * weights[k] 
            for k in weights.keys()
        )
        
        weighted_score = np.clip(weighted_score, -1.0, 1.0)
        
        logits = self._score_to_logits(weighted_score)
        probs = self._softmax(logits)
        
        primary_bias = self._get_primary_bias(probs)
        confidence = max(probs) * 100
        
        # Risk flags
        risk_flags = []
        if features.get('vol_expansion', 0) > 0.5:
            risk_flags.append("VOL_EXPANSION")
        if features.get('liquidity_deterioration', 0) > 0.5:
            risk_flags.append("LIQUIDITY_DETERIORATION")
        if features.get('volatility_regime', 0) < -0.7:
            risk_flags.append("HIGH_VOL_REGIME")
        
        # Feature lineage
        feature_lineage = {
            'vix_lookback_days': len(input_bundle.vix_daily),
            'correlation_window_days': 60,
            'breadth_sample_days': len(input_bundle.market_breadth_30d) if input_bundle.market_breadth_30d is not None else 0
        }
        
        features.update(feature_lineage)
        
        return PillarOutput(
            pillar_name="REGIME_CONTEXT",
            timestamp=datetime.now(),
            prob_strong_bullish=probs[4],
            prob_bullish=probs[3],
            prob_neutral=probs[2],
            prob_bearish=probs[1],
            prob_strong_bearish=probs[0],
            primary_bias=primary_bias,
            confidence=confidence,
            health=health,
            health_message=health_msg,
            feature_contributions=features,
            data_sources=["index_history", "market_breadth", "vix_data"],
            feature_version=self.feature_version,
            risk_flags=risk_flags
        )
    
    def _create_failed_output(self, symbol: str, message: str) -> PillarOutput:
        """Create neutral output when pillar fails."""
        return PillarOutput(
            pillar_name="REGIME_CONTEXT",
            timestamp=datetime.now(),
            prob_strong_bullish=0.0,
            prob_bullish=0.0,
            prob_neutral=1.0,
            prob_bearish=0.0,
            prob_strong_bearish=0.0,
            primary_bias=DirectionalBias.NEUTRAL,
            confidence=0.0,
            health=PillarHealth.FAILED,
            health_message=message,
            feature_contributions={},
            data_sources=[],
            feature_version=self.feature_version,
            risk_flags=["PILLAR_FAILED", "REGIME_UNKNOWN"]
        )
