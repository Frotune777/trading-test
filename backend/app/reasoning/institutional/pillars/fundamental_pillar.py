"""
PILLAR 5: Fundamental / Thematic Context

Analyzes earnings quality, balance sheet strength, and growth trajectory.

Ownership:
- Earnings quality (cash flow conversion)
- Balance sheet strength (debt/equity, current ratio)
- Growth trajectory (revenue/profit acceleration)
- Peer relative valuation

NO OVERLAP with price structure, institutional flow, or derivatives logic.
"""

import logging
from typing import Dict
import numpy as np
import pandas as pd
from datetime import datetime

from ..input_bundles import FundamentalInput
from .. import BasePillar, PillarOutput, PillarHealth, DirectionalBias

logger = logging.getLogger(__name__)


class FundamentalPillar(BasePillar):
    """
    Fundamental analysis using financial statement data.
    """
    
    def __init__(self, feature_version: str = "1.0.0"):
        super().__init__(feature_version)
        logger.info(f"Initialized FundamentalPillar v{feature_version}")
    
    def check_health(self, input_bundle: FundamentalInput) -> tuple[PillarHealth, str]:
        """Check if sufficient fundamental data is available."""
        if input_bundle.quarterly_results is None or len(input_bundle.quarterly_results) < 4:
            return PillarHealth.FAILED, "Insufficient quarterly results (need 4+ quarters)"
        
        if input_bundle.balance_sheet is None or len(input_bundle.balance_sheet) == 0:
            return PillarHealth.DEGRADED, "Missing balance sheet data"
        
        if input_bundle.cash_flow is None or len(input_bundle.cash_flow) == 0:
            return PillarHealth.DEGRADED, "Missing cash flow data"
        
        return PillarHealth.HEALTHY, None
    
    def analyze(self, input_bundle: FundamentalInput) -> PillarOutput:
        """Analyze fundamental strength and quality."""
        health, health_msg = self.check_health(input_bundle)
        
        if health == PillarHealth.FAILED:
            return self._create_failed_output(input_bundle.symbol, health_msg)
        
        # 1. EARNINGS QUALITY (cash flow conversion)
        earnings_quality = self._compute_earnings_quality(
            input_bundle.quarterly_results,
            input_bundle.cash_flow
        )
        
        # 2. BALANCE SHEET STRENGTH
        balance_sheet_strength = self._compute_balance_sheet_strength(
            input_bundle.balance_sheet,
            input_bundle.financial_ratios
        )
        
        # 3. GROWTH TRAJECTORY
        growth_trajectory = self._compute_growth_trajectory(
            input_bundle.quarterly_results
        )
        
        # 4. PEER RELATIVE VALUATION
        peer_valuation = self._compute_peer_valuation(
            input_bundle.peer_metrics,
            input_bundle.sector_pe,
            input_bundle.sector_pb
        )
        
        features = {
            'earnings_quality': earnings_quality['cf_conversion'],
            'earnings_consistency': earnings_quality['consistency'],
            'balance_sheet_strength': balance_sheet_strength['composite'],
            'debt_equity_score': balance_sheet_strength['de_score'],
            'growth_trajectory': growth_trajectory['acceleration'],
            'growth_consistency': growth_trajectory['consistency'],
            'peer_valuation': peer_valuation
        }
        
        return self._features_to_distribution(
            input_bundle.symbol,
            features,
            health,
            health_msg,
            input_bundle
        )
    
    def _compute_earnings_quality(self,
                                    quarterly_df: pd.DataFrame,
                                    cashflow_df: pd.DataFrame) -> Dict:
        """
        Measure earnings quality using cash flow conversion.
        
        High quality: Operating cash flow > Net profit
        Low quality: Profit without cash generation
        """
        if quarterly_df.empty:
            return {'cf_conversion': 0.0, 'consistency': 0.0}
        
        # Get latest quarter
        latest_quarter = quarterly_df.iloc[0]
        net_profit = latest_quarter.get('net_profit', 0)
        
        # Get operating cash flow (annual or latest available)
        if cashflow_df is not None and not cashflow_df.empty:
            latest_cf = cashflow_df.iloc[0]
            operating_cf = latest_cf.get('operating_cash_flow', 0)
        else:
            operating_cf = 0
        
        if net_profit == 0:
            cf_conversion = 0.0
        else:
            # Cash flow to profit ratio
            cf_ratio = operating_cf / (net_profit * 4)  # Annualize quarterly profit
            # Normalize: ratio > 1.0 = high quality
            cf_conversion = (cf_ratio - 1.0)
            cf_conversion = np.clip(cf_conversion, -1.0, 1.0)
        
        # Consistency: check if profits are growing consistently
        if len(quarterly_df) >= 4:
            profits = quarterly_df.head(4)['net_profit'].values
            growing_quarters = sum(profits[i] > profits[i+1] for i in range(len(profits)-1))
            consistency = (growing_quarters / 3.0) * 2 - 1  # Map to [-1, 1]
        else:
            consistency = 0.0
        
        return {
            'cf_conversion': cf_conversion,
            'consistency': consistency
        }
    
    def _compute_balance_sheet_strength(self,
                                          balance_df: pd.DataFrame,
                                          ratios_df: pd.DataFrame) -> Dict:
        """
        Analyze balance sheet leverage and liquidity.
        
        Low debt, high current ratio = strong
        """
        if balance_df is None or balance_df.empty:
            return {'composite': 0.0, 'de_score': 0.0}
        
        latest_bs = balance_df.iloc[0]
        
        # Debt to equity ratio
        debt = latest_bs.get('borrowings', 0) + latest_bs.get('total_liabilities', 0)
        equity = latest_bs.get('equity_capital', 0) + latest_bs.get('reserves', 0)
        
        if equity == 0:
            de_score = -1.0  # No equity = weak
        else:
            debt_to_equity = debt / equity
            # Low D/E (< 0.5) = strong, High D/E (> 2.0) = weak
            de_score = 1.0 - (debt_to_equity / 2.0)
            de_score = np.clip(de_score, -1.0, 1.0)
        
        # Current ratio
        if ratios_df is not None and not ratios_df.empty:
            latest_ratios = ratios_df.iloc[0]
            current_ratio = latest_ratios.get('current_ratio', 1.0)
            # Current ratio > 1.5 = strong, < 1.0 = weak
            cr_score = (current_ratio - 1.0) / 0.5
            cr_score = np.clip(cr_score, -1.0, 1.0)
        else:
            cr_score = 0.0
        
        # Composite score
        composite = (de_score + cr_score) / 2.0
        
        return {
            'composite': composite,
            'de_score': de_score
        }
    
    def _compute_growth_trajectory(self, quarterly_df: pd.DataFrame) -> Dict:
        """
        Analyze revenue and profit growth trend.
        
        Accelerating growth = bullish
        Decelerating = bearish
        """
        if len(quarterly_df) < 4:
            return {'acceleration': 0.0, 'consistency': 0.0}
        
        # Compute YoY growth for last 2 quarters
        q1_sales = quarterly_df.iloc[0].get('sales', 0)
        q1_yoy_sales = quarterly_df.iloc[4].get('sales', q1_sales) if len(quarterly_df) > 4 else q1_sales
        
        q2_sales = quarterly_df.iloc[1].get('sales', 0)
        q2_yoy_sales = quarterly_df.iloc[5].get('sales', q2_sales) if len(quarterly_df) > 5 else q2_sales
        
        if q1_yoy_sales == 0 or q2_yoy_sales == 0:
            return {'acceleration': 0.0, 'consistency': 0.0}
        
        q1_growth = (q1_sales / q1_yoy_sales - 1)
        q2_growth = (q2_sales / q2_yoy_sales - 1)
        
        # Growth acceleration
        acceleration = q1_growth - q2_growth
        
        # Normalize: ±10% acceleration = ±1.0
        normalized_accel = acceleration / 0.10
        normalized_accel = np.clip(normalized_accel, -1.0, 1.0)
        
        # Consistency: are all recent quarters growing?
        if len(quarterly_df) >= 4:
            sales = quarterly_df.head(4)['sales'].values
            growing_quarters = sum(sales[i] > sales[i+1] for i in range(len(sales)-1))
            consistency = (growing_quarters / 3.0) * 2 - 1  # Map to [-1, 1]
        else:
            consistency = 0.0
        
        return {
            'acceleration': normalized_accel,
            'consistency': consistency
        }
    
    def _compute_peer_valuation(self,
                                  peer_df: pd.DataFrame,
                                  sector_pe: float,
                                  sector_pb: float) -> float:
        """
        Compare valuation to peers and sector.
        
        Trading below peers = bullish (value)
        Trading above = bearish (expensive)
        """
        if peer_df is None or peer_df.empty or sector_pe == 0:
            return 0.0
        
        # Get company's own PE (assume first row is self)
        own_pe = peer_df.iloc[0].get('pe', sector_pe)
        
        # Compare to sector average
        pe_discount = (sector_pe - own_pe) / sector_pe if sector_pe > 0 else 0
        
        # Normalize: ±30% discount = ±1.0
        normalized = pe_discount / 0.30
        return np.clip(normalized, -1.0, 1.0)
    
    def _features_to_distribution(self,
                                    symbol: str,
                                    features: Dict[str, float],
                                    health: PillarHealth,
                                    health_msg: str,
                                    input_bundle: FundamentalInput) -> PillarOutput:
        """Convert fundamental features to probability distribution."""
        weights = {
            'earnings_quality': 0.25,
            'balance_sheet_strength': 0.25,
            'growth_trajectory': 0.30,
            'peer_valuation': 0.20
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
        if features.get('earnings_quality', 0) < -0.5:
            risk_flags.append("LOW_EARNINGS_QUALITY")
        if features.get('debt_equity_score', 0) < -0.5:
            risk_flags.append("HIGH_LEVERAGE")
        if features.get('growth_trajectory', 0) < -0.5:
            risk_flags.append("DECELERATING_GROWTH")
        
        # Feature lineage
        feature_lineage = {
            'quarters_analyzed': len(input_bundle.quarterly_results),
            'sector_name': input_bundle.sector_name,
            'sector_pe': input_bundle.sector_pe
        }
        
        features.update(feature_lineage)
        
        return PillarOutput(
            pillar_name="FUNDAMENTAL_THEMATIC",
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
            data_sources=["quarterly_results", "balance_sheet", "cash_flow", "financial_ratios"],
            feature_version=self.feature_version,
            risk_flags=risk_flags
        )
    
    def _create_failed_output(self, symbol: str, message: str) -> PillarOutput:
        """Create neutral output when pillar fails."""
        return PillarOutput(
            pillar_name="FUNDAMENTAL_THEMATIC",
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
