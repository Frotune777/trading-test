"""
Global Risk Governor

System-level risk gate for QUAD v2.
Operates OUTSIDE individual pillars.

FAIL-LOUD behavior is mandatory.

Rules:
1. If any CORE pillar is FAILED → decision INVALID
2. If ≥2 pillars are DEGRADED → conviction capped at 50%
3. If Regime pillar FAILED → no directional bias allowed (force NEUTRAL)
4. If Execution pillar FAILED → decision INVALID (not executable)
"""

import logging
from typing import List, Dict, Tuple
from enum import Enum

from . import PillarOutput, PillarHealth

logger = logging.getLogger(__name__)


class DecisionValidity(Enum):
    """Decision validity status."""
    VALID = "VALID"
    DEGRADED = "DEGRADED"
    INVALID = "INVALID"


class GlobalRiskGovernor:
    """
    System-level risk gate for QUAD decisions.
    
    This is the FINAL authority on whether a decision can be executed.
    No pillar can override these rules.
    """
    
    # Core pillars that MUST be healthy for valid decisions
    CORE_PILLARS = {
        "PRICE_STRUCTURE",
        "INSTITUTIONAL_FLOW",
        "DERIVATIVES_POSITIONING",
        "REGIME_CONTEXT"
    }
    
    # Critical pillar (regime) - if failed, force neutral
    REGIME_PILLAR = "REGIME_CONTEXT"
    
    # Execution pillar (must be healthy to execute)
    EXECUTION_PILLAR = "EXECUTION_FEASIBILITY"
    
    def __init__(self):
        logger.info("Initialized GlobalRiskGovernor")
    
    def validate_decision(self, 
                          pillar_outputs: List[PillarOutput]) -> Tuple[DecisionValidity, List[str]]:
        """
        Validate decision based on pillar health.
        
        This is the PRIMARY risk gate. All decisions must pass through here.
        
        Args:
            pillar_outputs: List of all 6 pillar outputs
            
        Returns:
            Tuple of (validity_status, blocking_reasons)
        """
        blocking_reasons = []
        
        # Convert to dict for easier lookup
        pillars_by_name = {p.pillar_name: p for p in pillar_outputs}
        
        # RULE 1: Check core pillar failures
        failed_core_pillars = [
            name for name in self.CORE_PILLARS
            if name in pillars_by_name and 
               pillars_by_name[name].health == PillarHealth.FAILED
        ]
        
        if failed_core_pillars:
            blocking_reasons.append(
                f"CRITICAL: Core pillar(s) FAILED: {', '.join(failed_core_pillars)}"
            )
            logger.error(f"Decision INVALID - core pillars failed: {failed_core_pillars}")
            return DecisionValidity.INVALID, blocking_reasons
        
        # RULE 2: Check execution pillar
        exec_pillar = pillars_by_name.get(self.EXECUTION_PILLAR)
        if exec_pillar and exec_pillar.health == PillarHealth.FAILED:
            blocking_reasons.append(
                "CRITICAL: Execution pillar FAILED - order not executable"
            )
            logger.error("Decision INVALID - execution not feasible")
            return DecisionValidity.INVALID, blocking_reasons
        
        # RULE 3: Check regime pillar (special case - doesn't block, but forces neutral)
        regime_pillar = pillars_by_name.get(self.REGIME_PILLAR)
        if regime_pillar and regime_pillar.health == PillarHealth.FAILED:
            blocking_reasons.append(
                "CRITICAL: Regime pillar FAILED - forcing NEUTRAL bias"
            )
            logger.warning("Regime pillar failed - will force neutral distribution")
            # Don't return INVALID, but flag for forced neutral
        
        # RULE 4: Count degraded pillars
        degraded_count = sum(
            1 for p in pillar_outputs 
            if p.health == PillarHealth.DEGRADED
        )
        
        if degraded_count >= 2:
            blocking_reasons.append(
                f"WARNING: {degraded_count}/6 pillars DEGRADED - conviction capped at 50%"
            )
            logger.warning(f"{degraded_count} pillars degraded - capping conviction")
            return DecisionValidity.DEGRADED, blocking_reasons
        
        # All checks passed
        if blocking_reasons:
            # Has regime failure but otherwise valid
            return DecisionValidity.DEGRADED, blocking_reasons
        else:
            logger.info("Decision validation passed - all pillars healthy")
            return DecisionValidity.VALID, []
    
    def apply_conviction_cap(self, 
                              base_confidence: float,
                              validity: DecisionValidity) -> float:
        """
        Apply conviction cap based on decision validity.
        
        Args:
            base_confidence: Original confidence score (0-100)
            validity: Decision validity status
            
        Returns:
            Capped confidence score
        """
        if validity == DecisionValidity.INVALID:
            logger.warning("Applying 0% conviction cap (INVALID decision)")
            return 0.0
        elif validity == DecisionValidity.DEGRADED:
            capped = min(base_confidence, 50.0)
            logger.info(f"Applying 50% conviction cap (DEGRADED): {base_confidence:.1f}% → {capped:.1f}%")
            return capped
        else:
            return base_confidence
    
    def force_neutral_if_regime_failed(self,
                                        pillar_outputs: List[PillarOutput],
                                        probs: List[float]) -> List[float]:
        """
        Force neutral distribution if regime pillar failed.
        
        This is a HARD override - if we don't know the regime, we cannot
        take directional bets.
        
        Args:
            pillar_outputs: All pillar outputs
            probs: Original probability distribution [strong_bearish, bearish, neutral, bullish, strong_bullish]
            
        Returns:
            Modified probability distribution (neutral if regime failed)
        """
        pillars_by_name = {p.pillar_name: p for p in pillar_outputs}
        regime_pillar = pillars_by_name.get(self.REGIME_PILLAR)
        
        if regime_pillar and regime_pillar.health == PillarHealth.FAILED:
            logger.warning("FORCING NEUTRAL DISTRIBUTION - regime pillar failed")
            # Force 100% neutral distribution
            return [0.0, 0.0, 1.0, 0.0, 0.0]
        
        return probs
    
    def check_execution_feasibility(self, pillar_outputs: List[PillarOutput]) -> Tuple[bool, List[str]]:
        """
        Check if order is executable based on execution pillar.
        
        Args:
            pillar_outputs: All pillar outputs
            
        Returns:
            Tuple of (is_executable, risk_flags)
        """
        pillars_by_name = {p.pillar_name: p for p in pillar_outputs}
        exec_pillar = pillars_by_name.get(self.EXECUTION_PILLAR)
        
        if not exec_pillar:
            logger.error("Execution pillar missing!")
            return False, ["EXECUTION_PILLAR_MISSING"]
        
        # Check for NOT_EXECUTABLE flag
        if "NOT_EXECUTABLE" in exec_pillar.risk_flags:
            logger.warning("Order NOT EXECUTABLE per execution pillar")
            return False, exec_pillar.risk_flags
        
        # Check for high risk flags
        high_risk_flags = [
            flag for flag in exec_pillar.risk_flags
            if flag in ["HIGH_SLIPPAGE", "HIGH_IMPACT_RISK", "LOW_LIQUIDITY_WINDOW"]
        ]
        
        if high_risk_flags:
            logger.warning(f"Execution has high risk: {high_risk_flags}")
            return True, high_risk_flags  # Executable but risky
        
        return True, []
    
    def collect_all_risk_flags(self, pillar_outputs: List[PillarOutput]) -> Dict[str, List[str]]:
        """
        Collect all risk flags from all pillars.
        
        Returns:
            Dict mapping pillar_name to list of risk flags
        """
        return {
            p.pillar_name: p.risk_flags
            for p in pillar_outputs
            if p.risk_flags
        }
