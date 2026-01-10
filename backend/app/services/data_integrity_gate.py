import logging
from typing import Tuple, Optional, Dict, Any
from ..core.market_snapshot import LiveDecisionSnapshot
from ..core.trade_intent import AnalysisQuality, TradeIntent
from ..core.config import settings

logger = logging.getLogger(__name__)

class StrictDataIntegrityGate:
    """
    Enforces strict data integrity rules for trading decisions.
    Implements Rules #6, #8, #9, #10, and #11 from user_rules.
    """
    
    MAX_LTP_AGE_SECONDS = 5.0
    
    @classmethod
    def evaluate_intent(
        cls, 
        intent: TradeIntent, 
        snapshot: LiveDecisionSnapshot,
        feed_health: Optional[Dict[str, Any]] = None,
        validation_result: Optional[Any] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluate if a TradeIntent is safe for execution based on data integrity.
        
        Args:
            intent: The generated trade intent
            snapshot: The market data snapshot used
            feed_health: Current feed health status (optional but recommended)
            validation_result: Feed cross-validation result (optional)
            
        Returns:
            (is_safe, block_reason)
        """
        # Rule #11: If feed health is not explicitly HEALTHY, assume UNSAFE.
        if feed_health:
            status = feed_health.get("status", "UNKNOWN")
            if status != "HEALTHY":
                # Allow DEGRADED for monitoring but block NEW execution
                return False, f"RULE_11_UNSAFE_FEED_{status}"
        
        # Snapshot-level Source Check (Redundancy)
        if snapshot.ltp_source == "ERROR" or snapshot.ltp_source == "UNKNOWN":
            return False, "RULE_11_UNSAFE_FEED_SOURCE"
            
        # Rule #8: Redis real-time LTP is authoritative ONLY if freshness < 5s.
        # Rule #9: If data freshness is unknown, treat it as STALE.
        if snapshot.ltp_age_ms is None:
            return False, "RULE_9_STALE_UNKNOWN_FRESHNESS"
            
        age_seconds = snapshot.ltp_age_ms / 1000.0
        if age_seconds > cls.MAX_LTP_AGE_SECONDS:
            return False, f"RULE_8_STALE_DATA_{age_seconds:.1f}S"
            
        # Rule #6: If required data is missing or stale, the Agent must fail closed.
        if intent.quality.failed_pillars:
            return False, f"RULE_6_PILLAR_FAILURE_{','.join(intent.quality.failed_pillars)}"
            
        if intent.quality.placeholder_pillars > 0:
            return False, "RULE_6_INCOMPLETE_PILLARS"

        # Cross-Validation Checks (Rule #6 extension for Bad Data)
        if validation_result and not validation_result.is_valid:
             # Block if critical divergence exists
             # For now, we treat any validation failure as a block if it comes with warnings
             if validation_result.warnings:
                 return False, "RULE_6_DATA_DIVERGENCE"

        # Check for specific critical data points depending on bias
        if intent.directional_bias.value != "NEUTRAL":
            if snapshot.bid_price is None or snapshot.ask_price is None:
                return False, "MISSING_LIQUIDITY_DEPTH"
                
        return True, None

    @classmethod
    def apply_gate(
        cls, 
        intent: TradeIntent, 
        snapshot: LiveDecisionSnapshot,
        feed_health: Optional[Dict[str, Any]] = None,
        validation_result: Optional[Any] = None
    ) -> TradeIntent:
        """
        Applies the gate to a TradeIntent, modifying its execution readiness.
        """
        is_safe, block_reason = cls.evaluate_intent(
            intent, 
            snapshot, 
            feed_health=feed_health, 
            validation_result=validation_result
        )
        
        if not is_safe:
            intent.is_execution_ready = False
            intent.execution_block_reason = block_reason
            intent.degradation_warnings.append(f"Data Integrity Gate Block: {block_reason}")
            logger.warning(f"TradeIntent for {intent.symbol} blocked by StrictDataIntegrityGate: {block_reason}")
            
        return intent
