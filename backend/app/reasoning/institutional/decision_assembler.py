"""
Bayesian Decision Assembler

Aggregates pillar probability distributions using Bayesian methods.
Applies regime-based dynamic weighting.
Computes risk envelope and execution constraints.

This is the FINAL step before decision persistence.
"""

import logging
from typing import List, Dict, Tuple
import numpy as np
from datetime import datetime

from . import PillarOutput, DirectionalBias
from .risk_governor import GlobalRiskGovernor, DecisionValidity

logger = logging.getLogger(__name__)


class BayesianDecisionAssembler:
    """
    Assembles final decision from 6 pillar outputs.
    
    Uses Bayesian aggregation with regime-based dynamic weighting.
    Prevents double-counting of volatility and liquidity.
    """
    
    def __init__(self, risk_governor: GlobalRiskGovernor = None):
        self.risk_governor = risk_governor or GlobalRiskGovernor()
        
        # Base weights (sum to 1.0)
        self.base_weights = {
            'PRICE_STRUCTURE': 0.20,
            'INSTITUTIONAL_FLOW': 0.20,
            'DERIVATIVES_POSITIONING': 0.15,
            'REGIME_CONTEXT': 0.15,
            'FUNDAMENTAL_THEMATIC': 0.15,
            'EXECUTION_FEASIBILITY': 0.15
        }
        
        logger.info("Initialized BayesianDecisionAssembler")
    
    def assemble(self, pillar_outputs: List[PillarOutput], symbol: str = 'UNKNOWN') -> Dict:
        """
        Combine pillar outputs into final decision.
        
        Steps:
        1. Validate decision via Risk Governor
        2. Adjust weights based on regime
        3. Aggregate probability distributions
        4. Force neutral if regime failed
        5. Compute risk envelope
        6. Apply conviction caps
        7. Check execution feasibility
        
        Args:
            pillar_outputs: List of all 6 pillar outputs
            symbol: Stock symbol being analyzed
            
        Returns:
            Dict containing final decision data
        """
        logger.info(f"Assembling decision from {len(pillar_outputs)} pillars")
        
        # 1. VALIDATE via Risk Governor
        validity, blocking_reasons = self.risk_governor.validate_decision(pillar_outputs)
        
        if validity == DecisionValidity.INVALID:
            logger.error(f"Decision INVALID: {blocking_reasons}")
            return self._create_invalid_decision(pillar_outputs, blocking_reasons, symbol)
        
        # 2. ADJUST WEIGHTS (regime-based)
        adjusted_weights = self._adjust_weights_for_regime(pillar_outputs)
        logger.info(f"Adjusted weights: {adjusted_weights}")
        
        # 3. AGGREGATE DISTRIBUTIONS
        final_probs = self._aggregate_distributions(pillar_outputs, adjusted_weights)
        
        # 4. FORCE NEUTRAL IF REGIME FAILED
        final_probs = self.risk_governor.force_neutral_if_regime_failed(
            pillar_outputs, final_probs
        )
        
        # 5. COMPUTE RISK ENVELOPE
        risk_envelope = self._compute_risk_envelope(pillar_outputs, final_probs)
        
        # 6. APPLY CONVICTION CAP
        base_confidence = max(final_probs) * 100
        capped_confidence = self.risk_governor.apply_conviction_cap(
            base_confidence, validity
        )
        
        # 7. CHECK EXECUTION FEASIBILITY
        is_executable, exec_risk_flags = self.risk_governor.check_execution_feasibility(
            pillar_outputs
        )
        
        # 8. DETERMINE PRIMARY BIAS
        primary_bias = self._get_primary_bias(final_probs)
        
        # 9. COLLECT ALL RISK FLAGS
        all_risk_flags = self.risk_governor.collect_all_risk_flags(pillar_outputs)
        
        # 10. ASSEMBLE DECISION
        decision = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            
            # Final probabilities
            'prob_strong_bearish': final_probs[0],
            'prob_bearish': final_probs[1],
            'prob_neutral': final_probs[2],
            'prob_bullish': final_probs[3],
            'prob_strong_bullish': final_probs[4],
            
            # Primary bias and confidence
            'primary_bias': primary_bias.value,
            'confidence': capped_confidence,
            'base_confidence': base_confidence,  # Before capping
            
            # Validity
            'validity': validity.value,
            'blocking_reasons': blocking_reasons,
            
            # Execution
            'is_executable': is_executable,
            'execution_risk_flags': exec_risk_flags,
            
            # Risk envelope
            **risk_envelope,
            
            # Pillar contributions
            'pillar_weights': adjusted_weights,
            'pillar_outputs': self._serialize_pillar_outputs(pillar_outputs),
            'all_risk_flags': all_risk_flags,
            
            # Metadata
            'num_healthy_pillars': sum(1 for p in pillar_outputs if p.health.value == 'HEALTHY'),
            'num_degraded_pillars': sum(1 for p in pillar_outputs if p.health.value == 'DEGRADED'),
            'num_failed_pillars': sum(1 for p in pillar_outputs if p.health.value == 'FAILED'),
        }
        
        logger.info(f"Decision assembled: {primary_bias.value} @ {capped_confidence:.1f}% confidence")
        return decision
    
    def _adjust_weights_for_regime(self, pillars: List[PillarOutput]) -> Dict[str, float]:
        """
        Adjust pillar weights based on regime context.
        
        High vol regime: Increase Regime weight, reduce Derivatives
        Low vol regime: Increase Fundamental weight, reduce Regime
        """
        weights = self.base_weights.copy()
        
        # Find regime pillar
        regime_pillar = next((p for p in pillars if p.pillar_name == "REGIME_CONTEXT"), None)
        
        if regime_pillar and regime_pillar.health.value == 'HEALTHY':
            # Check for high vol regime
            if "HIGH_VOL_REGIME" in regime_pillar.risk_flags:
                logger.info("High vol regime detected - adjusting weights")
                weights['REGIME_CONTEXT'] += 0.05
                weights['DERIVATIVES_POSITIONING'] -= 0.05
            
            # Check for low vol regime (volatility_regime > 0.5 means low VIX)
            vol_regime = regime_pillar.feature_contributions.get('volatility_regime', 0)
            if vol_regime > 0.5:
                logger.info("Low vol regime detected - adjusting weights")
                weights['FUNDAMENTAL_THEMATIC'] += 0.05
                weights['REGIME_CONTEXT'] -= 0.05
        
        # Renormalize to ensure sum = 1.0
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def _aggregate_distributions(self,
                                   pillars: List[PillarOutput],
                                   weights: Dict[str, float]) -> List[float]:
        """
        Weighted average of probability distributions.
        
        Returns:
            List of 5 probabilities [strong_bearish, bearish, neutral, bullish, strong_bullish]
        """
        agg_probs = [0.0, 0.0, 0.0, 0.0, 0.0]
        
        for pillar in pillars:
            weight = weights.get(pillar.pillar_name, 0.0)
            
            agg_probs[0] += pillar.prob_strong_bearish * weight
            agg_probs[1] += pillar.prob_bearish * weight
            agg_probs[2] += pillar.prob_neutral * weight
            agg_probs[3] += pillar.prob_bullish * weight
            agg_probs[4] += pillar.prob_strong_bullish * weight
        
        # Renormalize (should already sum to 1.0, but ensure)
        total = sum(agg_probs)
        if total > 0:
            agg_probs = [p / total for p in agg_probs]
        
        logger.debug(f"Aggregated probabilities: {agg_probs}")
        return agg_probs
    
    def _compute_risk_envelope(self,
                                pillars: List[PillarOutput],
                                final_probs: List[float]) -> Dict:
        """
        Compute position sizing and risk parameters.
        
        Returns dict with:
        - max_position_size: Confidence-adjusted position multiplier (0.25-1.0)
        - stop_loss_pct: Vol-adjusted stop loss
        - take_profit_pct: Expected move based on distribution
        - max_hold_days: Conviction-based holding period
        """
        confidence = max(final_probs)
        
        # 1. POSITION SIZE (scales with confidence)
        # Low confidence (0.3) = 25% of normal size
        # High confidence (0.8) = 100% of normal size
        position_multiplier = (confidence - 0.2) / 0.6
        position_multiplier = np.clip(position_multiplier, 0.25, 1.0)
        
        # 2. STOP LOSS (based on volatility regime)
        regime_pillar = next((p for p in pillars if p.pillar_name == "REGIME_CONTEXT"), None)
        if regime_pillar and "HIGH_VOL_REGIME" in regime_pillar.risk_flags:
            stop_loss_pct = 3.0  # Wider stop in high vol
        else:
            stop_loss_pct = 2.0  # Normal stop
        
        # 3. TAKE PROFIT (based on expected value)
        expected_value = sum([
            final_probs[0] * (-100),
            final_probs[1] * (-50),
            final_probs[2] * 0,
            final_probs[3] * 50,
            final_probs[4] * 100
        ])
        take_profit_pct = abs(expected_value) / 20  # Scale to reasonable %
        take_profit_pct = max(take_profit_pct, 3.0)  # Minimum 3%
        
        # 4. MAX HOLD PERIOD (based on conviction)
        max_hold_days = int(5 + confidence * 10)  # 5-15 days
        
        logger.info(f"Risk envelope: pos_size={position_multiplier:.2f}, stop={stop_loss_pct:.1f}%, tp={take_profit_pct:.1f}%")
        
        return {
            'max_position_size': position_multiplier,
            'stop_loss_pct': stop_loss_pct,
            'take_profit_pct': take_profit_pct,
            'max_hold_days': max_hold_days,
            'expected_value': expected_value
        }
    
    def _get_primary_bias(self, probs: List[float]) -> DirectionalBias:
        """Determine primary bias from probability distribution."""
        max_idx = probs.index(max(probs))
        return [
            DirectionalBias.STRONG_BEARISH,
            DirectionalBias.BEARISH,
            DirectionalBias.NEUTRAL,
            DirectionalBias.BULLISH,
            DirectionalBias.STRONG_BULLISH
        ][max_idx]
    
    def _serialize_pillar_outputs(self, pillars: List[PillarOutput]) -> Dict:
        """Convert pillar outputs to serializable dict."""
        return {
            p.pillar_name: {
                'primary_bias': p.primary_bias.value,
                'confidence': p.confidence,
                'health': p.health.value,
                'health_message': p.health_message,
                'feature_contributions': p.feature_contributions,
                'data_sources': p.data_sources,
                'feature_version': p.feature_version,
                'risk_flags': p.risk_flags
            }
            for p in pillars
        }
    
    def _create_invalid_decision(self, pillars: List[PillarOutput], reasons: List[str], symbol: str = 'UNKNOWN') -> Dict:
        """Create invalid decision when validation fails."""
        logger.error(f"Creating INVALID decision: {reasons}")
        
        return {
            'timestamp': datetime.now(),
            'symbol': symbol,
            
            # Neutral distribution
            'prob_strong_bearish': 0.0,
            'prob_bearish': 0.0,
            'prob_neutral': 1.0,
            'prob_bullish': 0.0,
            'prob_strong_bullish': 0.0,
            
            # Neutral bias, zero confidence
            'primary_bias': DirectionalBias.NEUTRAL.value,
            'confidence': 0.0,
            'base_confidence': 0.0,
            
            # Invalid status
            'validity': DecisionValidity.INVALID.value,
            'blocking_reasons': reasons,
            
            # Not executable
            'is_executable': False,
            'execution_risk_flags': ['DECISION_INVALID'],
            
            # Zero risk envelope
            'max_position_size': 0.0,
            'stop_loss_pct': 0.0,
            'take_profit_pct': 0.0,
            'max_hold_days': 0,
            'expected_value': 0.0,
            
            # Pillar data
            'pillar_weights': {},
            'pillar_outputs': self._serialize_pillar_outputs(pillars),
            'all_risk_flags': self.risk_governor.collect_all_risk_flags(pillars),
            
            # Metadata
            'num_healthy_pillars': sum(1 for p in pillars if p.health.value == 'HEALTHY'),
            'num_degraded_pillars': sum(1 for p in pillars if p.health.value == 'DEGRADED'),
            'num_failed_pillars': sum(1 for p in pillars if p.health.value == 'FAILED'),
        }
