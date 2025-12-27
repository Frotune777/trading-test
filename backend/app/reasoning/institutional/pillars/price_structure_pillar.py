"""
PILLAR 1: Price & Market Structure

Institutional-grade price structure analysis using:
- Price efficiency (variance ratio test)
- Auction dynamics
- Volatility-adjusted structure (Parkinson estimator)
- Liquidity provision patterns

NO RETAIL INDICATORS (SMA/RSI/MACD).
"""

import logging
from typing import Dict, List
import numpy as np
import pandas as pd
from datetime import datetime

from ..input_bundles import PriceStructureInput
from .. import BasePillar, PillarOutput, PillarHealth, DirectionalBias

logger = logging.getLogger(__name__)


class PriceStructurePillar(BasePillar):
    """
    Analyzes price efficiency, auction dynamics, and volatility-adjusted structure.
    
    Uses STRUCTURAL features only:
    - Variance ratio test (price efficiency)
    - Auction participation analysis
    - Parkinson volatility estimator
    - Bid/ask imbalance
    """
    
    def __init__(self, feature_version: str = "1.0.0"):
        super().__init__(feature_version)
        logger.info(f"Initialized PriceStructurePillar v{feature_version}")
    
    def check_health(self, input_bundle: PriceStructureInput) -> tuple[PillarHealth, str]:
        """
        Check if sufficient data is available.
        """
        if input_bundle.ohlcv_daily is None or len(input_bundle.ohlcv_daily) < 60:
            return PillarHealth.FAILED, "Insufficient price history (need 60+ days)"
        
        if input_bundle.upper_circuit == 0 or input_bundle.lower_circuit == 0:
            return PillarHealth.DEGRADED, "Circuit limits missing"
        
        if input_bundle.bid_levels is None or input_bundle.ask_levels is None:
            return PillarHealth.DEGRADED, "Market depth data missing"
        
        return PillarHealth.HEALTHY, None
    
    def analyze(self, input_bundle: PriceStructureInput) -> PillarOutput:
        """
        Compute structural features from price action.
        """
        # Check health first
        health, health_msg = self.check_health(input_bundle)
        
        if health == PillarHealth.FAILED:
            # Return neutral distribution if failed
            return self._create_failed_output(input_bundle.symbol, health_msg)
        
        # 1. PRICE EFFICIENCY ANALYSIS
        price_efficiency = self._compute_price_efficiency(input_bundle.ohlcv_daily)
        
        # 2. AUCTION DYNAMICS
        auction_strength = self._compute_auction_strength(
            input_bundle.opening_auction_volume,
            input_bundle.closing_auction_volume,
            input_bundle.ohlcv_daily
        )
        
        # 3. VOLATILITY-ADJUSTED STRUCTURE
        vol_adjusted_structure = self._compute_vol_adjusted_structure(
            input_bundle.ohlcv_daily
        )
        
        # 4. LIQUIDITY PROVISION PATTERN
        liquidity_pattern = self._compute_liquidity_pattern(
            input_bundle.bid_levels,
            input_bundle.ask_levels
        )
        
        # 5. CIRCUIT PROXIMITY
        circuit_risk = self._compute_circuit_risk(
            input_bundle.ohlcv_daily.iloc[-1]['close'],
            input_bundle.upper_circuit,
            input_bundle.lower_circuit
        )
        
        # COMBINE FEATURES INTO PROBABILITY DISTRIBUTION
        features = {
            'price_efficiency': price_efficiency,
            'auction_strength': auction_strength,
            'vol_adjusted_structure': vol_adjusted_structure,
            'liquidity_pattern': liquidity_pattern,
            'circuit_risk': circuit_risk
        }
        
        return self._features_to_distribution(
            input_bundle.symbol,
            features,
            health,
            health_msg
        )
    
    def _compute_price_efficiency(self, ohlcv: pd.DataFrame) -> float:
        """
        Measure price discovery efficiency using variance ratio test.
        
        Efficient markets: variance ratio ≈ 1.0
        Mean reversion: variance ratio < 1.0
        Momentum: variance ratio > 1.0
        
        Returns: -1.0 (mean reverting) to +1.0 (trending)
        """
        returns = ohlcv['close'].pct_change().dropna()
        
        if len(returns) < 10:
            return 0.0
        
        # Variance ratio test (Lo-MacKinlay)
        # Compare variance of k-period returns to k * variance of 1-period returns
        k = 5  # 5-day horizon
        
        var_1 = returns.var()
        var_k = returns.rolling(k).sum().var()
        
        if var_1 == 0 or pd.isna(var_k):
            return 0.0
            
        variance_ratio = var_k / (k * var_1)
        
        # Normalize to [-1, 1]
        # VR < 1 suggests mean reversion (bearish for momentum)
        # VR > 1 suggests trending (bullish for momentum)
        normalized = (variance_ratio - 1.0) / 0.5  # Assume VR typically in [0.5, 1.5]
        return np.clip(normalized, -1.0, 1.0)
    
    def _compute_auction_strength(self, 
                                   open_vol: int,
                                   close_vol: int,
                                   ohlcv: pd.DataFrame) -> float:
        """
        Analyze auction participation relative to continuous trading.
        
        High auction volume suggests institutional participation.
        
        Returns: 0.0 (weak) to 1.0 (strong)
        """
        if open_vol is None or close_vol is None:
            return 0.5  # Neutral if data missing
            
        avg_volume = ohlcv['volume'].tail(20).mean()
        
        if avg_volume == 0:
            return 0.5
            
        # Auction volume as % of daily average
        auction_pct = (open_vol + close_vol) / avg_volume
        
        # Normalize: 10% auction participation = neutral, 30%+ = strong
        normalized = (auction_pct - 0.10) / 0.20
        return np.clip(normalized, 0.0, 1.0)
    
    def _compute_vol_adjusted_structure(self, ohlcv: pd.DataFrame) -> float:
        """
        Analyze price structure adjusted for realized volatility.
        
        Uses Parkinson volatility estimator (high-low range).
        Compares recent range expansion to historical norm.
        
        Returns: -1.0 (contracting) to +1.0 (expanding)
        """
        # Parkinson volatility: sqrt(1/(4*ln(2)) * (ln(H/L))^2)
        hl_ratio = np.log(ohlcv['high'] / ohlcv['low'])
        parkinson_vol = np.sqrt((1 / (4 * np.log(2))) * (hl_ratio ** 2))
        
        # Recent volatility (last 5 days)
        recent_vol = parkinson_vol.tail(5).mean()
        
        # Historical volatility (last 60 days)
        hist_vol = parkinson_vol.tail(60).mean()
        
        if hist_vol == 0 or pd.isna(recent_vol) or pd.isna(hist_vol):
            return 0.0
            
        # Vol expansion ratio
        vol_ratio = (recent_vol / hist_vol) - 1.0
        
        # Normalize: ±30% vol change = ±1.0
        normalized = vol_ratio / 0.30
        return np.clip(normalized, -1.0, 1.0)
    
    def _compute_liquidity_pattern(self,
                                    bid_levels: List[tuple],
                                    ask_levels: List[tuple]) -> float:
        """
        Analyze bid/ask imbalance and depth quality.
        
        Returns: -1.0 (ask-heavy, bearish) to +1.0 (bid-heavy, bullish)
        """
        if not bid_levels or not ask_levels:
            return 0.0
            
        # Total bid quantity
        total_bid_qty = sum(qty for _, qty in bid_levels)
        
        # Total ask quantity
        total_ask_qty = sum(qty for _, qty in ask_levels)
        
        if total_bid_qty + total_ask_qty == 0:
            return 0.0
            
        # Imbalance ratio
        imbalance = (total_bid_qty - total_ask_qty) / (total_bid_qty + total_ask_qty)
        
        return imbalance  # Already in [-1, 1]
    
    def _compute_circuit_risk(self, current_price: float,
                               upper_circuit: float,
                               lower_circuit: float) -> str:
        """
        Check proximity to circuit limits.
        
        Returns: "UPPER_CIRCUIT_RISK" | "LOWER_CIRCUIT_RISK" | "NORMAL"
        """
        # Within 2% of upper circuit
        if current_price >= upper_circuit * 0.98:
            return "UPPER_CIRCUIT_RISK"
            
        # Within 2% of lower circuit
        if current_price <= lower_circuit * 1.02:
            return "LOWER_CIRCUIT_RISK"
            
        return "NORMAL"
    
    def _features_to_distribution(self,
                                    symbol: str,
                                    features: Dict[str, float],
                                    health: PillarHealth,
                                    health_msg: str) -> PillarOutput:
        """
        Convert structural features to probability distribution.
        
        Uses Bayesian approach to combine multiple signals.
        """
        # Weighted combination of features
        weights = {
            'price_efficiency': 0.30,
            'auction_strength': 0.20,
            'vol_adjusted_structure': 0.25,
            'liquidity_pattern': 0.25
        }
        
        # Compute weighted score (-1 to +1)
        weighted_score = sum(
            features[k] * weights[k] 
            for k in weights.keys()
            if k in features and isinstance(features[k], (int, float))
        )
        
        # Convert to probability distribution using softmax
        # Map score to 5-class probabilities
        logits = self._score_to_logits(weighted_score)
        probs = self._softmax(logits)
        
        # Determine primary bias
        primary_bias = self._get_primary_bias(probs)
        
        # Confidence = max probability
        confidence = max(probs) * 100
        
        # Risk flags
        risk_flags = []
        if features.get('circuit_risk') != "NORMAL":
            risk_flags.append(features['circuit_risk'])
            
        return PillarOutput(
            pillar_name="PRICE_STRUCTURE",
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
            data_sources=["price_history", "market_depth", "latest_snapshot"],
            feature_version=self.feature_version,
            risk_flags=risk_flags
        )
    
    def _create_failed_output(self, symbol: str, message: str) -> PillarOutput:
        """
        Create neutral output when pillar fails.
        """
        return PillarOutput(
            pillar_name="PRICE_STRUCTURE",
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
            risk_flags=["PILLAR_FAILED"]
        )
