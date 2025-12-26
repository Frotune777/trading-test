"""
Cross-Broker Data Validation
Validates data consistency across multiple brokers.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import statistics

from app.brokers.base_adapter import BrokerType

logger = logging.getLogger(__name__)


class CrossBrokerValidator:
    """
    Cross-Broker Data Validation
    
    Features:
        - LTP consensus validation
        - Outlier detection
        - Data quality scoring
        - Broker reliability tracking
    """
    
    def __init__(self):
        self.validation_history: List[Dict[str, Any]] = []
        self.broker_reliability: Dict[BrokerType, float] = {}
        
        logger.info("CrossBrokerValidator initialized")
    
    def validate_ltp(
        self,
        symbol: str,
        ltp_data: Dict[BrokerType, float],
        threshold_percent: float = 0.5
    ) -> Dict[str, Any]:
        """
        Validate LTP data across brokers.
        
        Args:
            symbol: Stock symbol
            ltp_data: Dict of broker -> LTP
            threshold_percent: Outlier threshold (default 0.5%)
            
        Returns:
            Validation result with consensus, outliers, and quality score
        """
        if not ltp_data or len(ltp_data) < 2:
            return {
                "valid": False,
                "reason": "Insufficient data for validation",
                "consensus_ltp": None,
                "quality_score": 0.0
            }
        
        prices = list(ltp_data.values())
        
        # Calculate consensus (median)
        consensus_ltp = statistics.median(prices)
        
        # Detect outliers
        outliers = []
        for broker, ltp in ltp_data.items():
            deviation_percent = abs((ltp - consensus_ltp) / consensus_ltp * 100)
            
            if deviation_percent > threshold_percent:
                outliers.append({
                    "broker": broker.value,
                    "ltp": ltp,
                    "deviation_percent": deviation_percent
                })
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(
            len(ltp_data),
            len(outliers),
            prices
        )
        
        # Determine validity
        valid = len(outliers) <= len(ltp_data) // 2  # More than half agree
        
        result = {
            "valid": valid,
            "symbol": symbol,
            "consensus_ltp": consensus_ltp,
            "broker_count": len(ltp_data),
            "outlier_count": len(outliers),
            "outliers": outliers,
            "quality_score": quality_score,
            "timestamp": datetime.now().isoformat()
        }
        
        # Record validation
        self.validation_history.append(result)
        
        # Update broker reliability
        self._update_reliability(ltp_data, outliers)
        
        if outliers:
            logger.warning(
                f"LTP validation for {symbol}: {len(outliers)} outliers detected. "
                f"Consensus: {consensus_ltp}"
            )
        else:
            logger.debug(f"LTP validation for {symbol}: All brokers agree (±{threshold_percent}%)")
        
        return result
    
    def validate_historical_data(
        self,
        symbol: str,
        data_sources: Dict[BrokerType, Any]
    ) -> Dict[str, Any]:
        """
        Validate historical data consistency across brokers.
        
        Args:
            symbol: Stock symbol
            data_sources: Dict of broker -> DataFrame
            
        Returns:
            Validation result
        """
        if not data_sources or len(data_sources) < 2:
            return {
                "valid": False,
                "reason": "Insufficient data sources"
            }
        
        # Compare candle counts
        candle_counts = {
            broker: len(df) for broker, df in data_sources.items()
        }
        
        # Check if counts are similar (within 10%)
        counts = list(candle_counts.values())
        avg_count = statistics.mean(counts)
        
        mismatches = []
        for broker, count in candle_counts.items():
            deviation_percent = abs((count - avg_count) / avg_count * 100)
            if deviation_percent > 10:
                mismatches.append({
                    "broker": broker.value,
                    "count": count,
                    "expected": int(avg_count),
                    "deviation_percent": deviation_percent
                })
        
        valid = len(mismatches) == 0
        
        result = {
            "valid": valid,
            "symbol": symbol,
            "candle_counts": {b.value: c for b, c in candle_counts.items()},
            "mismatches": mismatches,
            "timestamp": datetime.now().isoformat()
        }
        
        if mismatches:
            logger.warning(
                f"Historical data validation for {symbol}: "
                f"{len(mismatches)} brokers have mismatched candle counts"
            )
        
        return result
    
    def get_most_reliable_broker(
        self,
        available_brokers: List[BrokerType]
    ) -> Optional[BrokerType]:
        """
        Get most reliable broker based on validation history.
        
        Args:
            available_brokers: List of available brokers
            
        Returns:
            Most reliable broker or None
        """
        if not available_brokers:
            return None
        
        # Filter to available brokers with reliability scores
        candidates = [
            (broker, self.broker_reliability.get(broker, 0.5))
            for broker in available_brokers
            if broker in self.broker_reliability
        ]
        
        if not candidates:
            # No reliability data, return first available
            return available_brokers[0]
        
        # Sort by reliability (highest first)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        most_reliable = candidates[0][0]
        logger.info(
            f"Most reliable broker: {most_reliable.value} "
            f"(reliability: {candidates[0][1]:.2%})"
        )
        
        return most_reliable
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary statistics"""
        if not self.validation_history:
            return {
                "total_validations": 0,
                "average_quality_score": 0.0,
                "broker_reliability": {}
            }
        
        recent_validations = self.validation_history[-100:]  # Last 100
        
        return {
            "total_validations": len(self.validation_history),
            "recent_validations": len(recent_validations),
            "average_quality_score": statistics.mean(
                [v["quality_score"] for v in recent_validations]
            ),
            "average_outliers": statistics.mean(
                [v["outlier_count"] for v in recent_validations]
            ),
            "broker_reliability": {
                b.value: score for b, score in self.broker_reliability.items()
            }
        }
    
    def _calculate_quality_score(
        self,
        broker_count: int,
        outlier_count: int,
        prices: List[float]
    ) -> float:
        """
        Calculate data quality score (0.0 to 1.0).
        
        Factors:
            - Number of brokers (more is better)
            - Outlier ratio (fewer is better)
            - Price variance (lower is better)
        """
        # Broker count score (max 6 brokers)
        broker_score = min(broker_count / 6.0, 1.0)
        
        # Outlier score
        outlier_ratio = outlier_count / broker_count if broker_count > 0 else 1.0
        outlier_score = 1.0 - outlier_ratio
        
        # Variance score
        if len(prices) > 1:
            variance = statistics.variance(prices)
            mean_price = statistics.mean(prices)
            cv = (variance ** 0.5) / mean_price if mean_price > 0 else 1.0
            variance_score = max(0.0, 1.0 - (cv * 100))  # Lower CV is better
        else:
            variance_score = 0.5
        
        # Weighted average
        quality_score = (
            broker_score * 0.3 +
            outlier_score * 0.5 +
            variance_score * 0.2
        )
        
        return round(quality_score, 3)
    
    def _update_reliability(
        self,
        ltp_data: Dict[BrokerType, float],
        outliers: List[Dict[str, Any]]
    ):
        """Update broker reliability scores"""
        outlier_brokers = {o["broker"] for o in outliers}
        
        for broker in ltp_data.keys():
            current_reliability = self.broker_reliability.get(broker, 0.5)
            
            if broker.value in outlier_brokers:
                # Decrease reliability
                new_reliability = current_reliability * 0.95
            else:
                # Increase reliability
                new_reliability = min(current_reliability * 1.05, 1.0)
            
            self.broker_reliability[broker] = new_reliability


# Global singleton instance
cross_broker_validator = CrossBrokerValidator()
