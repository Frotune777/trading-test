"""
PILLAR 2: Institutional Flow

Analyzes FII/DII activity, bulk/block deals, and insider accumulation.

Ownership:
- FII/DII net flow (level + acceleration)
- Bulk & block deal clustering
- Insider accumulation/distribution patterns

Detects:
- Flow persistence vs exhaustion
- Alignment or divergence with price

NO OVERLAP with derivatives, volatility, or execution logic.
"""

import logging
from typing import Dict
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from ..input_bundles import InstitutionalFlowInput
from .. import BasePillar, PillarOutput, PillarHealth, DirectionalBias

logger = logging.getLogger(__name__)


class InstitutionalFlowPillar(BasePillar):
    """
    Analyzes institutional participation and accumulation patterns.
    
    Uses STRUCTURAL features only:
    - FII/DII flow persistence and acceleration
    - Bulk/block deal clustering
    - Insider accumulation patterns
    - Shareholding pattern shifts
    """
    
    def __init__(self, feature_version: str = "1.0.0"):
        super().__init__(feature_version)
        logger.info(f"Initialized InstitutionalFlowPillar v{feature_version}")
    
    def check_health(self, input_bundle: InstitutionalFlowInput) -> tuple[PillarHealth, str]:
        """
        Check if sufficient institutional flow data is available.
        """
        # Check FII/DII data
        if input_bundle.fii_net_30d is None or len(input_bundle.fii_net_30d) < 10:
            return PillarHealth.FAILED, "Insufficient FII/DII data (need 10+ days)"
        
        if input_bundle.dii_net_30d is None or len(input_bundle.dii_net_30d) < 10:
            return PillarHealth.FAILED, "Insufficient DII data (need 10+ days)"
        
        # Bulk/block deals are optional but preferred
        has_deals = (
            input_bundle.bulk_deals_30d is not None and len(input_bundle.bulk_deals_30d) > 0
        ) or (
            input_bundle.block_deals_30d is not None and len(input_bundle.block_deals_30d) > 0
        )
        
        # Insider data is optional but preferred
        has_insider = (
            input_bundle.insider_trades_90d is not None and 
            len(input_bundle.insider_trades_90d) > 0
        )
        
        if not has_deals and not has_insider:
            return PillarHealth.DEGRADED, "Missing bulk/block and insider data"
        
        return PillarHealth.HEALTHY, None
    
    def analyze(self, input_bundle: InstitutionalFlowInput) -> PillarOutput:
        """
        Analyze institutional participation and flow patterns.
        """
        # Check health first
        health, health_msg = self.check_health(input_bundle)
        
        if health == PillarHealth.FAILED:
            return self._create_failed_output(input_bundle.symbol, health_msg)
        
        # 1. FII/DII FLOW ANALYSIS (level + acceleration)
        fii_dii_signal = self._compute_fii_dii_flow(
            input_bundle.fii_net_30d,
            input_bundle.dii_net_30d
        )
        
        # 2. BULK/BLOCK DEAL CLUSTERING
        large_deal_signal = self._compute_large_deal_clustering(
            input_bundle.bulk_deals_30d,
            input_bundle.block_deals_30d
        )
        
        # 3. INSIDER ACCUMULATION PATTERN
        insider_signal = self._compute_insider_pattern(
            input_bundle.insider_trades_90d
        )
        
        # 4. SHAREHOLDING PATTERN SHIFT
        shareholding_signal = self._compute_shareholding_shift(
            input_bundle.shareholding_latest,
            input_bundle.shareholding_prev_quarter
        )
        
        # COMBINE SIGNALS
        features = {
            'fii_dii_flow': fii_dii_signal['score'],
            'fii_dii_acceleration': fii_dii_signal['acceleration'],
            'fii_dii_persistence': fii_dii_signal['persistence'],
            'large_deal_clustering': large_deal_signal['score'],
            'deal_cluster_strength': large_deal_signal['cluster_strength'],
            'insider_accumulation': insider_signal['score'],
            'insider_conviction': insider_signal['conviction'],
            'shareholding_shift': shareholding_signal
        }
        
        return self._features_to_distribution(
            input_bundle.symbol,
            features,
            health,
            health_msg,
            input_bundle
        )
    
    def _compute_fii_dii_flow(self, fii_df: pd.DataFrame, dii_df: pd.DataFrame) -> Dict:
        """
        Analyze FII/DII net flow with level, acceleration, and persistence.
        
        Returns dict with:
        - score: -1.0 (strong selling) to +1.0 (strong buying)
        - acceleration: flow rate of change
        - persistence: consistency of flow direction
        """
        # Compute net flow (buy - sell)
        fii_net = fii_df['fii_net_value'].values
        dii_net = dii_df['dii_net_value'].values
        
        total_net = fii_net + dii_net
        
        # 1. FLOW LEVEL (recent 5 days vs 30-day average)
        recent_flow = total_net[-5:].sum()
        avg_flow = total_net.mean()
        
        # Normalize by standard deviation
        flow_std = total_net.std()
        if flow_std > 0:
            flow_level = (recent_flow / 5 - avg_flow) / flow_std
        else:
            flow_level = 0.0
        
        flow_level = np.clip(flow_level, -1.0, 1.0)
        
        # 2. FLOW ACCELERATION (is flow accelerating or decelerating?)
        if len(total_net) >= 10:
            recent_5 = total_net[-5:].mean()
            prev_5 = total_net[-10:-5].mean()
            
            if abs(prev_5) > 0:
                acceleration = (recent_5 - prev_5) / abs(prev_5)
            else:
                acceleration = 0.0
        else:
            acceleration = 0.0
        
        acceleration = np.clip(acceleration, -1.0, 1.0)
        
        # 3. FLOW PERSISTENCE (how consistent is the direction?)
        # Count days with same sign as overall direction
        overall_direction = np.sign(total_net.sum())
        if overall_direction != 0:
            same_direction_days = (np.sign(total_net) == overall_direction).sum()
            persistence = (same_direction_days / len(total_net)) * 2 - 1  # Map to [-1, 1]
        else:
            persistence = 0.0
        
        return {
            'score': flow_level,
            'acceleration': acceleration,
            'persistence': persistence
        }
    
    def _compute_large_deal_clustering(self, 
                                        bulk_df: pd.DataFrame, 
                                        block_df: pd.DataFrame) -> Dict:
        """
        Analyze bulk/block deal clustering and concentration.
        
        Returns dict with:
        - score: -1.0 (distribution) to +1.0 (accumulation)
        - cluster_strength: concentration of deals in time
        """
        # Combine bulk and block deals
        if bulk_df is None:
            bulk_df = pd.DataFrame()
        if block_df is None:
            block_df = pd.DataFrame()
            
        all_deals = pd.concat([bulk_df, block_df])
        
        if all_deals.empty:
            return {'score': 0.0, 'cluster_strength': 0.0}
        
        # 1. NET FLOW (buy vs sell)
        buy_qty = all_deals[all_deals['deal_type'] == 'buy']['quantity'].sum()
        sell_qty = all_deals[all_deals['deal_type'] == 'sell']['quantity'].sum()
        
        total_qty = buy_qty + sell_qty
        
        if total_qty == 0:
            return {'score': 0.0, 'cluster_strength': 0.0}
        
        net_imbalance = (buy_qty - sell_qty) / total_qty
        
        # 2. CLUSTERING STRENGTH (are deals concentrated in recent days?)
        if 'deal_date' in all_deals.columns:
            all_deals['deal_date'] = pd.to_datetime(all_deals['deal_date'])
            recent_cutoff = datetime.now() - timedelta(days=7)
            
            recent_deals = all_deals[all_deals['deal_date'] >= recent_cutoff]
            recent_qty = recent_deals['quantity'].sum()
            
            if total_qty > 0:
                cluster_strength = recent_qty / total_qty
            else:
                cluster_strength = 0.0
        else:
            cluster_strength = 0.5  # Unknown
        
        return {
            'score': net_imbalance,
            'cluster_strength': cluster_strength
        }
    
    def _compute_insider_pattern(self, insider_df: pd.DataFrame) -> Dict:
        """
        Analyze insider buying/selling pattern and conviction.
        
        Returns dict with:
        - score: -1.0 (selling) to +1.0 (buying)
        - conviction: strength of insider conviction (based on promoter activity)
        """
        if insider_df is None or insider_df.empty:
            return {'score': 0.0, 'conviction': 0.0}
        
        # Filter for promoters and directors only (key insiders)
        key_insiders = insider_df[
            insider_df['person_category'].isin(['Promoter', 'Director'])
        ]
        
        if key_insiders.empty:
            return {'score': 0.0, 'conviction': 0.0}
        
        # 1. NET VALUE (buy vs sell)
        buy_value = key_insiders[key_insiders['transaction_type'] == 'buy']['value'].sum()
        sell_value = key_insiders[key_insiders['transaction_type'] == 'sell']['value'].sum()
        
        total_value = buy_value + sell_value
        
        if total_value == 0:
            return {'score': 0.0, 'conviction': 0.0}
        
        net_imbalance = (buy_value - sell_value) / total_value
        
        # 2. CONVICTION (number of distinct promoters buying)
        if 'person_name' in key_insiders.columns:
            buy_insiders = key_insiders[key_insiders['transaction_type'] == 'buy']
            num_buyers = buy_insiders['person_name'].nunique()
            
            # Multiple promoters buying = high conviction
            conviction = min(num_buyers / 3.0, 1.0)  # 3+ promoters = max conviction
        else:
            conviction = 0.5  # Unknown
        
        return {
            'score': net_imbalance,
            'conviction': conviction
        }
    
    def _compute_shareholding_shift(self, 
                                     latest: Dict[str, float],
                                     prev: Dict[str, float]) -> float:
        """
        Analyze change in institutional shareholding.
        
        Increasing FII/DII shareholding = bullish.
        
        Returns: -1.0 (decreasing) to +1.0 (increasing)
        """
        if latest is None or prev is None:
            return 0.0
        
        # Compute change in FII + DII shareholding
        fii_change = latest.get('fii', 0) - prev.get('fii', 0)
        dii_change = latest.get('dii', 0) - prev.get('dii', 0)
        
        total_change = fii_change + dii_change
        
        # Normalize: ±5% change = ±1.0
        normalized = total_change / 5.0
        return np.clip(normalized, -1.0, 1.0)
    
    def _features_to_distribution(self,
                                    symbol: str,
                                    features: Dict[str, float],
                                    health: PillarHealth,
                                    health_msg: str,
                                    input_bundle: InstitutionalFlowInput) -> PillarOutput:
        """
        Convert institutional flow features to probability distribution.
        """
        # Weighted combination of features
        weights = {
            'fii_dii_flow': 0.25,
            'fii_dii_acceleration': 0.15,
            'fii_dii_persistence': 0.10,
            'large_deal_clustering': 0.20,
            'insider_accumulation': 0.20,
            'shareholding_shift': 0.10
        }
        
        # Compute weighted score (-1 to +1)
        weighted_score = sum(
            features.get(k, 0.0) * weights[k] 
            for k in weights.keys()
        )
        
        # Boost score if multiple signals align
        alignment_bonus = 0.0
        if (features.get('fii_dii_flow', 0) > 0 and 
            features.get('large_deal_clustering', 0) > 0 and
            features.get('insider_accumulation', 0) > 0):
            alignment_bonus = 0.2  # All buying
        elif (features.get('fii_dii_flow', 0) < 0 and 
              features.get('large_deal_clustering', 0) < 0 and
              features.get('insider_accumulation', 0) < 0):
            alignment_bonus = -0.2  # All selling
        
        weighted_score += alignment_bonus
        weighted_score = np.clip(weighted_score, -1.0, 1.0)
        
        # Convert to probability distribution
        logits = self._score_to_logits(weighted_score)
        probs = self._softmax(logits)
        
        primary_bias = self._get_primary_bias(probs)
        confidence = max(probs) * 100
        
        # Risk flags
        risk_flags = []
        if features.get('fii_dii_persistence', 0) < -0.5:
            risk_flags.append("FLOW_EXHAUSTION")
        if abs(features.get('fii_dii_acceleration', 0)) > 0.7:
            risk_flags.append("FLOW_ACCELERATION")
        
        # Feature lineage
        feature_lineage = {
            'fii_dii_lookback_days': len(input_bundle.fii_net_30d) if input_bundle.fii_net_30d is not None else 0,
            'bulk_deal_count': len(input_bundle.bulk_deals_30d) if input_bundle.bulk_deals_30d is not None else 0,
            'block_deal_count': len(input_bundle.block_deals_30d) if input_bundle.block_deals_30d is not None else 0,
            'insider_trade_count': len(input_bundle.insider_trades_90d) if input_bundle.insider_trades_90d is not None else 0,
            'data_freshness_hours': 24  # Assume daily data
        }
        
        features.update(feature_lineage)
        
        return PillarOutput(
            pillar_name="INSTITUTIONAL_FLOW",
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
            data_sources=["fii_dii_activity", "bulk_deals", "block_deals", "insider_trading", "shareholding"],
            feature_version=self.feature_version,
            risk_flags=risk_flags
        )
    
    def _create_failed_output(self, symbol: str, message: str) -> PillarOutput:
        """
        Create neutral output when pillar fails.
        """
        return PillarOutput(
            pillar_name="INSTITUTIONAL_FLOW",
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
