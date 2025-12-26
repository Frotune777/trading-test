"""
Enhanced Failover Logic
Priority-based broker selection with intelligent fallback.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.brokers.base_adapter import BrokerType, BrokerAdapter, HealthStatus
from app.core.app_config import app_config

logger = logging.getLogger(__name__)


class BrokerFailoverManager:
    """
    Enhanced Failover Manager
    
    Features:
        - Priority-based broker selection
        - Health-aware routing
        - Automatic broker rotation
        - Failure tracking and recovery
        - Cost optimization
    """
    
    def __init__(self):
        self.broker_priorities: Dict[BrokerType, int] = {}
        self.broker_health: Dict[BrokerType, HealthStatus] = {}
        self.failure_counts: Dict[BrokerType, int] = {}
        self.last_failure_time: Dict[BrokerType, datetime] = {}
        self.recovery_timeout = timedelta(minutes=5)
        
        # Load priorities from config
        self._load_priorities()
        
        logger.info("BrokerFailoverManager initialized")
    
    def _load_priorities(self):
        """Load broker priorities from configuration"""
        # Default priorities (lower number = higher priority)
        default_priorities = {
            BrokerType.ZERODHA: 1,
            BrokerType.ANGELONE: 2,
            BrokerType.FYERS: 3,
            BrokerType.UPSTOX: 4,
            BrokerType.DHAN: 5,
            BrokerType.FINVASIA: 6
        }
        
        # Load from config if available
        for broker_name, priority in default_priorities.items():
            config = app_config.get_broker_config(broker_name.value)
            if config:
                self.broker_priorities[broker_name] = config.priority
            else:
                self.broker_priorities[broker_name] = priority
    
    def select_best_broker(
        self,
        available_brokers: List[BrokerType],
        exclude: Optional[List[BrokerType]] = None,
        prefer_low_cost: bool = False
    ) -> Optional[BrokerType]:
        """
        Select best broker based on priority, health, and cost.
        
        Args:
            available_brokers: List of available broker types
            exclude: Brokers to exclude from selection
            prefer_low_cost: Prefer brokers with lower costs
            
        Returns:
            Selected broker type or None
        """
        if not available_brokers:
            return None
        
        exclude = exclude or []
        candidates = [b for b in available_brokers if b not in exclude]
        
        if not candidates:
            return None
        
        # Filter out unhealthy brokers
        healthy_candidates = []
        for broker in candidates:
            health = self.broker_health.get(broker, HealthStatus.UNKNOWN)
            
            # Check if broker is in recovery timeout
            if broker in self.last_failure_time:
                time_since_failure = datetime.now() - self.last_failure_time[broker]
                if time_since_failure < self.recovery_timeout:
                    logger.debug(f"Broker {broker.value} still in recovery timeout")
                    continue
            
            # Include HEALTHY and DEGRADED brokers
            if health in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]:
                healthy_candidates.append(broker)
        
        # If no healthy candidates, use all candidates (emergency fallback)
        if not healthy_candidates:
            logger.warning("No healthy brokers available, using all candidates")
            healthy_candidates = candidates
        
        # Sort by priority (lower number = higher priority)
        sorted_brokers = sorted(
            healthy_candidates,
            key=lambda b: (
                self.broker_priorities.get(b, 999),
                self.failure_counts.get(b, 0)
            )
        )
        
        # If prefer low cost, prioritize Finvasia (zero brokerage)
        if prefer_low_cost and BrokerType.FINVASIA in sorted_brokers:
            return BrokerType.FINVASIA
        
        selected = sorted_brokers[0]
        logger.info(f"Selected broker: {selected.value} (priority: {self.broker_priorities.get(selected, 999)})")
        
        return selected
    
    def record_failure(self, broker: BrokerType):
        """Record broker failure"""
        self.failure_counts[broker] = self.failure_counts.get(broker, 0) + 1
        self.last_failure_time[broker] = datetime.now()
        
        logger.warning(
            f"Recorded failure for {broker.value} "
            f"(total: {self.failure_counts[broker]})"
        )
    
    def record_success(self, broker: BrokerType):
        """Record broker success (resets failure count)"""
        if broker in self.failure_counts:
            self.failure_counts[broker] = 0
        if broker in self.last_failure_time:
            del self.last_failure_time[broker]
    
    def update_health(self, broker: BrokerType, health: HealthStatus):
        """Update broker health status"""
        self.broker_health[broker] = health
        
        if health == HealthStatus.HEALTHY:
            self.record_success(broker)
    
    def get_failover_sequence(
        self,
        primary: BrokerType,
        available_brokers: List[BrokerType]
    ) -> List[BrokerType]:
        """
        Get failover sequence starting from primary.
        
        Args:
            primary: Primary broker
            available_brokers: All available brokers
            
        Returns:
            Ordered list of brokers to try
        """
        sequence = [primary]
        
        # Add other brokers in priority order
        other_brokers = [b for b in available_brokers if b != primary]
        sorted_others = sorted(
            other_brokers,
            key=lambda b: self.broker_priorities.get(b, 999)
        )
        
        sequence.extend(sorted_others)
        
        return sequence
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get failover manager status summary"""
        return {
            "broker_priorities": {
                b.value: p for b, p in self.broker_priorities.items()
            },
            "broker_health": {
                b.value: h.value for b, h in self.broker_health.items()
            },
            "failure_counts": {
                b.value: c for b, c in self.failure_counts.items()
            },
            "brokers_in_recovery": [
                b.value for b in self.last_failure_time.keys()
                if datetime.now() - self.last_failure_time[b] < self.recovery_timeout
            ]
        }


# Global singleton instance
failover_manager = BrokerFailoverManager()
