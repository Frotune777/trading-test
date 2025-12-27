"""
PILLAR 3: Derivatives & Positioning

Analyzes gamma exposure, dealer positioning, and futures basis.

Ownership:
- Gamma exposure profiles
- Dealer positioning inference (via put-call skew)
- Futures basis & rollover stress
- IV term structure

Detects:
- Gamma traps
- Pin risk
- Volatility compression/expansion risk

NO OVERLAP with institutional flow, fundamental, or execution logic.
"""

import logging
from typing import Dict
import numpy as np
import pandas as pd
from datetime import datetime

from ..input_bundles import DerivativesInput
from .. import BasePillar, PillarOutput, PillarHealth, DirectionalBias

logger = logging.getLogger(__name__)


class DerivativesPillar(BasePillar):
    """
    Analyzes derivatives market structure and positioning.
    
    Uses STRUCTURAL features only:
    - Net gamma exposure
    - Put-call skew (dealer positioning proxy)
    - Futures basis (contango/backwardation)
    - IV term structure slope
    """
    
    def __init__(self, feature_version: str = "1.0.0"):
        super().__init__(feature_version)
        logger.info(f"Initialized DerivativesPillar v{feature_version}")
    
    def check_health(self, input_bundle: DerivativesInput) -> tuple[PillarHealth, str]:
        """
        Check if sufficient derivatives data is available.
        """
        if input_bundle.option_chain_current is None or len(input_bundle.option_chain_current) < 5:
            return PillarHealth.FAILED, "Insufficient option chain data"
        
        if input_bundle.futures_current is None or len(input_bundle.futures_current) == 0:
            return PillarHealth.DEGRADED, "Missing futures data"
        
        if input_bundle.spot_price == 0:
            return PillarHealth.FAILED, "Missing spot price"
        
        return PillarHealth.HEALTHY, None
    
    def analyze(self, input_bundle: DerivativesInput) -> PillarOutput:
        """
        Analyze derivatives positioning and risk.
        """
        health, health_msg = self.check_health(input_bundle)
        
        if health == PillarHealth.FAILED:
            return self._create_failed_output(input_bundle.symbol, health_msg)
        
        # 1. GAMMA EXPOSURE PROFILE
        gamma_signal = self._compute_gamma_exposure(
            input_bundle.option_chain_current,
            input_bundle.spot_price
        )
        
        # 2. DEALER POSITIONING (via put-call skew)
        dealer_signal = self._compute_dealer_positioning(
            input_bundle.option_chain_current
        )
        
        # 3. FUTURES BASIS
        basis_signal = self._compute_futures_basis(
            input_bundle.futures_current,
            input_bundle.spot_price
        )
        
        # 4. IV TERM STRUCTURE
        iv_signal = self._compute_iv_term_structure(
            input_bundle.option_chain_current,
            input_bundle.option_chain_next
        )
        
        features = {
            'gamma_exposure': gamma_signal['net_gamma'],
            'gamma_concentration': gamma_signal['concentration'],
            'dealer_positioning': dealer_signal['skew'],
            'dealer_confidence': dealer_signal['confidence'],
            'futures_basis': basis_signal['basis_pct'],
            'basis_stress': basis_signal['stress'],
            'iv_term_slope': iv_signal['slope'],
            'iv_inversion_risk': iv_signal['inversion_risk']
        }
        
        return self._features_to_distribution(
            input_bundle.symbol,
            features,
            health,
            health_msg,
            input_bundle
        )
    
    def _compute_gamma_exposure(self, option_chain: pd.DataFrame, spot: float) -> Dict:
        """
        Compute net gamma exposure around current spot.
        
        Large gamma = potential for explosive moves (gamma trap).
        """
        # Filter options within ±10% of spot
        atm_range = option_chain[
            (option_chain['strike_price'] >= spot * 0.90) &
            (option_chain['strike_price'] <= spot * 1.10)
        ]
        
        if atm_range.empty:
            return {'net_gamma': 0.0, 'concentration': 0.0}
        
        # Compute net gamma (call gamma - put gamma)
        call_gamma = atm_range[atm_range['option_type'] == 'CE']['gamma'].sum()
        put_gamma = atm_range[atm_range['option_type'] == 'PE']['gamma'].sum()
        
        net_gamma = call_gamma - put_gamma
        total_gamma = abs(call_gamma) + abs(put_gamma)
        
        if total_gamma == 0:
            return {'net_gamma': 0.0, 'concentration': 0.0}
        
        # Normalized net gamma
        net_gamma_norm = net_gamma / total_gamma
        
        # Concentration: how much gamma is concentrated at specific strikes?
        if 'open_interest' in atm_range.columns:
            oi_std = atm_range.groupby('strike_price')['open_interest'].sum().std()
            oi_mean = atm_range.groupby('strike_price')['open_interest'].sum().mean()
            concentration = oi_std / oi_mean if oi_mean > 0 else 0.0
        else:
            concentration = 0.5
        
        return {
            'net_gamma': np.clip(net_gamma_norm, -1.0, 1.0),
            'concentration': min(concentration, 1.0)
        }
    
    def _compute_dealer_positioning(self, option_chain: pd.DataFrame) -> Dict:
        """
        Infer dealer positioning from put-call IV skew.
        
        Positive skew (puts expensive) = dealers short puts = bullish.
        """
        # Get ATM options (delta between 0.45-0.55 for calls, -0.55 to -0.45 for puts)
        if 'delta' not in option_chain.columns or 'iv' not in option_chain.columns:
            return {'skew': 0.0, 'confidence': 0.0}
        
        atm_calls = option_chain[
            (option_chain['option_type'] == 'CE') &
            (option_chain['delta'].between(0.45, 0.55))
        ]
        
        atm_puts = option_chain[
            (option_chain['option_type'] == 'PE') &
            (option_chain['delta'].between(-0.55, -0.45))
        ]
        
        if atm_calls.empty or atm_puts.empty:
            return {'skew': 0.0, 'confidence': 0.0}
        
        avg_call_iv = atm_calls['iv'].mean()
        avg_put_iv = atm_puts['iv'].mean()
        
        skew = avg_put_iv - avg_call_iv
        
        # Normalize: ±5% IV skew = ±1.0
        normalized_skew = skew / 0.05
        normalized_skew = np.clip(normalized_skew, -1.0, 1.0)
        
        # Confidence based on sample size
        confidence = min((len(atm_calls) + len(atm_puts)) / 10.0, 1.0)
        
        return {
            'skew': normalized_skew,
            'confidence': confidence
        }
    
    def _compute_futures_basis(self, futures_df: pd.DataFrame, spot: float) -> Dict:
        """
        Analyze futures basis (futures - spot).
        
        Negative basis (backwardation) = bullish (short covering).
        Excessive contango = bearish (carry trade).
        """
        if futures_df.empty or spot == 0:
            return {'basis_pct': 0.0, 'stress': 0.0}
        
        # Get current month futures price
        current_futures = futures_df.iloc[0]['futures_price']
        
        basis = current_futures - spot
        basis_pct = (basis / spot) * 100
        
        # Stress: how far from normal basis?
        # Normal basis for NSE: 0.5-1.5% (cost of carry)
        normal_basis = 1.0
        stress = abs(basis_pct - normal_basis) / 2.0  # ±2% deviation = max stress
        stress = min(stress, 1.0)
        
        # Normalize basis: -2% to +2%
        # Negative basis (backwardation) = bullish
        normalized_basis = -basis_pct / 2.0
        normalized_basis = np.clip(normalized_basis, -1.0, 1.0)
        
        return {
            'basis_pct': normalized_basis,
            'stress': stress
        }
    
    def _compute_iv_term_structure(self, 
                                     current_expiry: pd.DataFrame,
                                     next_expiry: pd.DataFrame) -> Dict:
        """
        Analyze IV term structure slope.
        
        Inverted (current > next) = fear/uncertainty.
        """
        if current_expiry is None or next_expiry is None:
            return {'slope': 0.0, 'inversion_risk': 0.0}
        
        if current_expiry.empty or next_expiry.empty:
            return {'slope': 0.0, 'inversion_risk': 0.0}
        
        if 'iv' not in current_expiry.columns or 'iv' not in next_expiry.columns:
            return {'slope': 0.0, 'inversion_risk': 0.0}
        
        # Get ATM IV for both expiries
        current_atm_iv = current_expiry['iv'].median()
        next_atm_iv = next_expiry['iv'].median()
        
        if pd.isna(current_atm_iv) or pd.isna(next_atm_iv) or current_atm_iv == 0:
            return {'slope': 0.0, 'inversion_risk': 0.0}
        
        # Slope = (next - current) / current
        slope = (next_atm_iv - current_atm_iv) / current_atm_iv
        
        # Inversion risk (current > next)
        inversion_risk = 1.0 if slope < 0 else 0.0
        
        # Normalize slope: ±20% = ±1.0
        normalized_slope = slope / 0.20
        normalized_slope = np.clip(normalized_slope, -1.0, 1.0)
        
        return {
            'slope': normalized_slope,
            'inversion_risk': inversion_risk
        }
    
    def _features_to_distribution(self,
                                    symbol: str,
                                    features: Dict[str, float],
                                    health: PillarHealth,
                                    health_msg: str,
                                    input_bundle: DerivativesInput) -> PillarOutput:
        """
        Convert derivatives features to probability distribution.
        """
        weights = {
            'gamma_exposure': 0.25,
            'dealer_positioning': 0.30,
            'futures_basis': 0.25,
            'iv_term_slope': 0.20
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
        if features.get('gamma_concentration', 0) > 0.7:
            risk_flags.append("GAMMA_TRAP_RISK")
        if features.get('iv_inversion_risk', 0) > 0:
            risk_flags.append("IV_INVERSION")
        if features.get('basis_stress', 0) > 0.7:
            risk_flags.append("BASIS_STRESS")
        
        # Feature lineage
        feature_lineage = {
            'option_strikes_analyzed': len(input_bundle.option_chain_current) if input_bundle.option_chain_current is not None else 0,
            'futures_contracts': len(input_bundle.futures_current) if input_bundle.futures_current is not None else 0,
            'pcr_oi': input_bundle.pcr_oi,
            'iv_percentile': input_bundle.iv_percentile
        }
        
        features.update(feature_lineage)
        
        return PillarOutput(
            pillar_name="DERIVATIVES_POSITIONING",
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
            data_sources=["option_chain", "futures_data", "option_chain_summary"],
            feature_version=self.feature_version,
            risk_flags=risk_flags
        )
    
    def _create_failed_output(self, symbol: str, message: str) -> PillarOutput:
        """Create neutral output when pillar fails."""
        return PillarOutput(
            pillar_name="DERIVATIVES_POSITIONING",
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
