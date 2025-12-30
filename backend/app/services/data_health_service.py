"""
Data Health Monitoring Service
Monitors data freshness, drift, and quality
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.redis import redis_client
from app.core.openalgo_bridge import openalgo_client
from app.database.models_monitoring import SystemHealth

logger = logging.getLogger(__name__)


class DataHealthService:
    """
    Monitor data quality and freshness.
    
    Features:
    - LTP freshness monitoring (Rule #8: <5s for real-time)
    - Price drift detection between sources
    - Data quality checks
    - Feed health tracking
    """
    
    # Thresholds
    MAX_LTP_AGE_SECONDS = 5  # Rule #8: Real-time data must be <5s old
    MAX_DRIFT_BPS = 10  # Maximum acceptable drift in basis points
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_ltp_freshness(self, symbol: str) -> Dict[str, Any]:
        """
        Check if LTP data is fresh enough for trading.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with freshness status and age
        """
        try:
            # Get LTP from Redis
            redis_key = f"market:ltp:NSE:{symbol}"
            cached = await redis_client.get(redis_key)
            
            if not cached:
                return {
                    "symbol": symbol,
                    "fresh": False,
                    "reason": "NO_DATA",
                    "age_seconds": None
                }
            
            data = json.loads(cached)
            timestamp = data.get("timestamp")
            
            if not timestamp:
                return {
                    "symbol": symbol,
                    "fresh": False,
                    "reason": "NO_TIMESTAMP",
                    "age_seconds": None
                }
            
            # Calculate age
            ltp_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            age_seconds = (datetime.now(ltp_time.tzinfo) - ltp_time).total_seconds()
            
            is_fresh = age_seconds <= self.MAX_LTP_AGE_SECONDS
            
            return {
                "symbol": symbol,
                "fresh": is_fresh,
                "reason": "OK" if is_fresh else "STALE",
                "age_seconds": age_seconds,
                "ltp": data.get("ltp"),
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error checking LTP freshness for {symbol}: {e}")
            return {
                "symbol": symbol,
                "fresh": False,
                "reason": "ERROR",
                "error": str(e)
            }
    
    async def check_price_drift(
        self,
        symbol: str,
        redis_ltp: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Check for price drift between Redis and OpenAlgo.
        
        Args:
            symbol: Stock symbol
            redis_ltp: Optional Redis LTP (will fetch if not provided)
            
        Returns:
            Dict with drift status and metrics
        """
        try:
            # Get Redis LTP if not provided
            if redis_ltp is None:
                redis_key = f"market:ltp:NSE:{symbol}"
                cached = await redis_client.get(redis_key)
                if cached:
                    redis_ltp = json.loads(cached).get("ltp")
            
            if not redis_ltp:
                return {
                    "symbol": symbol,
                    "has_drift": False,
                    "reason": "NO_REDIS_DATA"
                }
            
            # Get OpenAlgo LTP
            openalgo_ltp = openalgo_client.get_ltp(symbol)
            
            if not openalgo_ltp:
                return {
                    "symbol": symbol,
                    "has_drift": False,
                    "reason": "NO_OPENALGO_DATA"
                }
            
            # Calculate drift in basis points
            drift_bps = abs((redis_ltp - openalgo_ltp) / openalgo_ltp * 10000)
            has_drift = drift_bps > self.MAX_DRIFT_BPS
            
            return {
                "symbol": symbol,
                "has_drift": has_drift,
                "drift_bps": drift_bps,
                "redis_ltp": redis_ltp,
                "openalgo_ltp": openalgo_ltp,
                "threshold_bps": self.MAX_DRIFT_BPS,
                "status": "DRIFT_DETECTED" if has_drift else "OK"
            }
            
        except Exception as e:
            logger.error(f"Error checking price drift for {symbol}: {e}")
            return {
                "symbol": symbol,
                "has_drift": False,
                "reason": "ERROR",
                "error": str(e)
            }
    
    async def get_feed_health(self) -> Dict[str, Any]:
        """
        Get overall feed health status.
        
        Returns:
            Dict with feed health metrics
        """
        try:
            status = openalgo_client.get_status()
            
            return {
                "feed_state": status.get("feed_state", "UNKNOWN"),
                "connected": status.get("connected", False),
                "symbols_subscribed": status.get("symbols_subscribed", 0),
                "last_update": status.get("last_update"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting feed health: {e}")
            return {
                "feed_state": "ERROR",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_data_quality(self, symbol: str) -> Dict[str, Any]:
        """
        Perform comprehensive data quality checks.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with quality check results
        """
        checks = {}
        
        # 1. Freshness check
        freshness = await self.check_ltp_freshness(symbol)
        checks["freshness"] = freshness
        
        # 2. Drift check
        drift = await self.check_price_drift(symbol)
        checks["drift"] = drift
        
        # 3. Overall status
        is_healthy = (
            freshness.get("fresh", False) and
            not drift.get("has_drift", True)
        )
        
        return {
            "symbol": symbol,
            "healthy": is_healthy,
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_stale_symbols(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Get list of symbols with stale data.
        
        Args:
            symbols: List of symbols to check
            
        Returns:
            List of stale symbol details
        """
        stale_symbols = []
        
        for symbol in symbols:
            freshness = await self.check_ltp_freshness(symbol)
            if not freshness.get("fresh", False):
                stale_symbols.append(freshness)
        
        return stale_symbols
    
    async def record_health_metric(
        self,
        metric_name: str,
        metric_value: float,
        unit: str = "",
        status: str = "HEALTHY"
    ):
        """
        Record system health metric to database.
        
        Args:
            metric_name: Name of the metric
            metric_value: Metric value
            unit: Unit of measurement
            status: Health status (HEALTHY, WARNING, CRITICAL)
        """
        try:
            health_record = SystemHealth(
                metric_name=metric_name,
                metric_value=metric_value,
                unit=unit,
                status=status,
                timestamp=datetime.now()
            )
            
            self.db.add(health_record)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to record health metric: {e}")
            await self.db.rollback()
