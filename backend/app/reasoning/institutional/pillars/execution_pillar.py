"""
PILLAR 6: Execution & Feasibility

Validates execution feasibility using order book depth, spread, and liquidity analysis.

Ownership:
- Order book depth analysis
- Bid-ask spread
- Time-of-day liquidity
- Historical slippage proxy

Outputs:
- EXECUTABLE / NOT_EXECUTABLE flag
- Expected slippage (bps)
- Liquidity risk flags

NO OVERLAP with price structure, derivatives, or regime logic.
"""

import logging
from typing import Dict
import numpy as np
import pandas as pd
from datetime import datetime, time

from ..input_bundles import ExecutionInput
from .. import BasePillar, PillarOutput, PillarHealth, DirectionalBias

logger = logging.getLogger(__name__)


class ExecutionPillar(BasePillar):
    """
    Execution feasibility and cost analysis.
    """
    
    def __init__(self, feature_version: str = "1.0.0"):
        super().__init__(feature_version)
        logger.info(f"Initialized ExecutionPillar v{feature_version}")
    
    def check_health(self, input_bundle: ExecutionInput) -> tuple[PillarHealth, str]:
        """Check if sufficient execution data is available."""
        if input_bundle.current_price == 0:
            return PillarHealth.FAILED, "Missing current price"
        
        if input_bundle.current_spread_bps == 0:
            return PillarHealth.DEGRADED, "Missing spread data"
        
        if input_bundle.avg_daily_volume_20d == 0:
            return PillarHealth.DEGRADED, "Missing volume data"
        
        return PillarHealth.HEALTHY, None
    
    def analyze(self, input_bundle: ExecutionInput) -> PillarOutput:
        """Assess execution feasibility and expected costs."""
        health, health_msg = self.check_health(input_bundle)
        
        if health == PillarHealth.FAILED:
            return self._create_failed_output(input_bundle.symbol, health_msg)
        
        # 1. SLIPPAGE ESTIMATION
        slippage_cost = self._estimate_slippage(
            input_bundle.current_spread_bps,
            input_bundle.recent_trades
        )
        
        # 2. MARKET IMPACT
        market_impact = self._estimate_market_impact(
            input_bundle.depth_snapshots_1h,
            input_bundle.avg_daily_volume_20d,
            input_bundle.current_volume
        )
        
        # 3. TIME-OF-DAY LIQUIDITY
        tod_liquidity = self._compute_tod_liquidity(
            input_bundle.time_to_close_minutes,
            input_bundle.is_trading_hours
        )
        
        # 4. ORDER BOOK RESILIENCE
        book_resilience = self._compute_book_resilience(
            input_bundle.depth_snapshots_1h
        )
        
        features = {
            'slippage_bps': slippage_cost['expected_bps'],
            'slippage_quality': slippage_cost['quality'],
            'market_impact': market_impact['impact_score'],
            'depth_adequacy': market_impact['depth_adequacy'],
            'tod_liquidity': tod_liquidity,
            'book_resilience': book_resilience,
            'is_executable': self._determine_executability(slippage_cost, market_impact, tod_liquidity)
        }
        
        return self._features_to_distribution(
            input_bundle.symbol,
            features,
            health,
            health_msg,
            input_bundle
        )
    
    def _estimate_slippage(self, spread_bps: float, recent_trades: pd.DataFrame) -> Dict:
        """
        Estimate expected slippage from spread and recent trades.
        
        Returns dict with:
        - expected_bps: Expected slippage in basis points
        - quality: 0.0 (poor) to 1.0 (excellent)
        """
        # Base slippage = half the spread (assuming mid-price execution)
        base_slippage = spread_bps / 2.0
        
        # Quality score based on spread
        # Spread < 10 bps = excellent
        # Spread > 50 bps = poor
        if spread_bps < 10:
            quality = 1.0
        elif spread_bps > 50:
            quality = 0.0
        else:
            quality = 1.0 - ((spread_bps - 10) / 40)
        
        return {
            'expected_bps': base_slippage,
            'quality': quality
        }
    
    def _estimate_market_impact(self,
                                  depth_df: pd.DataFrame,
                                  avg_volume: int,
                                  current_volume: int) -> Dict:
        """
        Estimate market impact for typical order size.
        
        Assume order size = 1% of daily volume.
        """
        if avg_volume == 0:
            return {'impact_score': 0.5, 'depth_adequacy': 0.5}
        
        # Typical order size (1% of daily volume)
        typical_order = avg_volume * 0.01
        
        # Current volume as % of average
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0.5
        
        # High current volume = low impact
        # Low current volume = high impact
        if volume_ratio > 1.5:
            impact_score = 1.0  # Very liquid
        elif volume_ratio < 0.5:
            impact_score = 0.3  # Illiquid
        else:
            impact_score = 0.5 + (volume_ratio - 1.0) * 0.5
        
        # Depth adequacy (placeholder - would analyze actual depth)
        depth_adequacy = 0.7  # Assume generally adequate
        
        return {
            'impact_score': np.clip(impact_score, 0.0, 1.0),
            'depth_adequacy': depth_adequacy
        }
    
    def _compute_tod_liquidity(self, time_to_close: int, is_trading_hours: bool) -> float:
        """
        Adjust for time-of-day liquidity patterns.
        
        Opening/closing hours = high liquidity
        Mid-day = lower liquidity
        
        Returns: 0.0 (poor timing) to 1.0 (good timing)
        """
        if not is_trading_hours:
            return 0.0  # Cannot execute outside trading hours
        
        # NSE trading hours: 09:15 - 15:30 (375 minutes)
        # First/last 30 minutes = high liquidity
        if time_to_close <= 30 or time_to_close >= 345:
            return 1.0
        # Mid-day (11:00 - 14:00) = lower liquidity
        elif 120 <= time_to_close <= 240:
            return 0.6
        else:
            return 0.8
    
    def _compute_book_resilience(self, depth_df: pd.DataFrame) -> float:
        """
        Measure order book resilience (how quickly it replenishes).
        
        Returns: 0.0 (fragile) to 1.0 (resilient)
        """
        # Placeholder: would measure depth replenishment rate
        # For now, assume moderate resilience
        return 0.7
    
    def _determine_executability(self,
                                   slippage: Dict,
                                   impact: Dict,
                                   tod_liquidity: float) -> bool:
        """
        Determine if order is executable based on cost and liquidity.
        
        NOT EXECUTABLE if:
        - Slippage > 50 bps
        - Market impact too high
        - Outside trading hours
        """
        if slippage['expected_bps'] > 50:
            return False
        
        if impact['impact_score'] < 0.3:
            return False
        
        if tod_liquidity == 0.0:
            return False
        
        return True
    
    def _features_to_distribution(self,
                                    symbol: str,
                                    features: Dict[str, float],
                                    health: PillarHealth,
                                    health_msg: str,
                                    input_bundle: ExecutionInput) -> PillarOutput:
        """
        Convert execution features to probability distribution.
        
        NOTE: Execution pillar outputs FEASIBILITY, not directional bias.
        High feasibility = can execute with low cost.
        """
        # Execution pillar is NEUTRAL on direction
        # It only assesses feasibility
        weights = {
            'slippage_quality': 0.30,
            'market_impact': 0.30,
            'tod_liquidity': 0.20,
            'book_resilience': 0.20
        }
        
        # Compute composite feasibility score
        feasibility_score = sum(
            features.get(k, 0.0) * weights[k] 
            for k in weights.keys()
        )
        
        feasibility_score = np.clip(feasibility_score, 0.0, 1.0)
        
        # Map feasibility to neutral-biased distribution
        # High feasibility = high confidence in neutral (can execute)
        # Low feasibility = low confidence (cannot execute reliably)
        if feasibility_score > 0.7:
            probs = [0.0, 0.0, 1.0, 0.0, 0.0]  # High confidence neutral
        elif feasibility_score > 0.4:
            probs = [0.0, 0.2, 0.6, 0.2, 0.0]  # Moderate confidence
        else:
            probs = [0.2, 0.2, 0.2, 0.2, 0.2]  # Low confidence (uncertain)
        
        primary_bias = DirectionalBias.NEUTRAL
        confidence = feasibility_score * 100
        
        # Risk flags
        risk_flags = []
        if not features.get('is_executable', True):
            risk_flags.append("NOT_EXECUTABLE")
        if features.get('slippage_bps', 0) > 30:
            risk_flags.append("HIGH_SLIPPAGE")
        if features.get('market_impact', 0) < 0.4:
            risk_flags.append("HIGH_IMPACT_RISK")
        if features.get('tod_liquidity', 0) < 0.5:
            risk_flags.append("LOW_LIQUIDITY_WINDOW")
        
        # Feature lineage
        feature_lineage = {
            'current_spread_bps': input_bundle.current_spread_bps,
            'avg_daily_volume': input_bundle.avg_daily_volume_20d,
            'is_trading_hours': input_bundle.is_trading_hours,
            'time_to_close_minutes': input_bundle.time_to_close_minutes
        }
        
        features.update(feature_lineage)
        
        return PillarOutput(
            pillar_name="EXECUTION_FEASIBILITY",
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
            data_sources=["market_depth", "intraday_prices", "latest_snapshot"],
            feature_version=self.feature_version,
            risk_flags=risk_flags
        )
    
    def _create_failed_output(self, symbol: str, message: str) -> PillarOutput:
        """Create neutral output when pillar fails."""
        return PillarOutput(
            pillar_name="EXECUTION_FEASIBILITY",
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
            risk_flags=["PILLAR_FAILED", "NOT_EXECUTABLE"]
        )
