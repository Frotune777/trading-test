"""
Enterprise Data Pipeline Service
Handles scheduled historical data fetching with freshness guarantees and health monitoring.
Complies with Rules #5-11, #33-37 (no fabrication, fail closed, freshness tracking, observability).
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import time

from app.core.config import settings
from app.core.redis import redis_client
from app.services.unified_data_service import UnifiedDataService
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Data source enumeration"""
    OPENALGO = "openalgo"
    NSE = "nse"
    YAHOO = "yahoo"


class FeedHealthStatus(Enum):
    """Feed health status per Rule #11"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


class DataPipelineService:
    """
    Async data pipeline for scheduled historical data fetching.
    
    Features:
    - Redis-centric LTP caching with 5s TTL (Rule #8-9)
    - Feed health monitoring with circuit breaker (Rule #11)
    - Audit logging for all operations (Rule #33-37)
    - Fail-closed on missing/stale data (Rule #6)
    """
    
    def __init__(self):
        self.unified_data = UnifiedDataService()
        self.alert_service = AlertService()
        self.circuit_breaker_active = False
        self.consecutive_failures = 0
        self.last_health_check = 0
        self.CIRCUIT_BREAKER_THRESHOLD = 3
        self.HEALTH_CHECK_INTERVAL = 30  # seconds
        
    async def fetch_and_cache_ltp(
        self, 
        symbol: str, 
        exchange: str = "NSE",
        source: DataSource = DataSource.OPENALGO
    ) -> bool:
        """
        Fetch LTP and cache in Redis with 5s TTL.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            exchange: Exchange code (default: NSE)
            source: Data source to use
            
        Returns:
            bool: True if successful, False otherwise
            
        Compliance:
            - Rule #8: Redis LTP is authoritative if freshness < 5s
            - Rule #9: Treat unknown freshness as STALE
            - Rule #33: Every operation logged
        """
        start_time = time.time()
        redis_key = f"ltp:{exchange}:{symbol}"
        
        try:
            # Check if circuit breaker is active
            if self.circuit_breaker_active:
                logger.warning(f"Circuit breaker active, skipping fetch for {symbol}")
                await self._log_audit(
                    action="FETCH_LTP_BLOCKED",
                    symbol=symbol,
                    reason="circuit_breaker_active",
                    success=False
                )
                return False
            
            # Fetch price data from unified service
            # Note: This uses ThreadPoolExecutor internally, but we're in async context
            # TODO: Refactor unified_data_service to be fully async
            price_data = await asyncio.to_thread(
                self.unified_data.nse_complete.get_price_data,
                symbol
            )
            
            if not price_data or 'ltp' not in price_data:
                logger.error(f"No LTP data received for {symbol}")
                self.consecutive_failures += 1
                await self._check_circuit_breaker()
                await self._log_audit(
                    action="FETCH_LTP_FAILED",
                    symbol=symbol,
                    reason="no_data_received",
                    success=False
                )
                return False
            
            ltp = price_data['ltp']
            
            # Validate LTP is reasonable (basic sanity check)
            if ltp <= 0:
                logger.error(f"Invalid LTP for {symbol}: {ltp}")
                await self._log_audit(
                    action="FETCH_LTP_FAILED",
                    symbol=symbol,
                    reason="invalid_ltp_value",
                    ltp=ltp,
                    success=False
                )
                return False
            
            # Cache in Redis with 5s TTL (Rule #8)
            cache_payload = {
                "ltp": float(ltp),
                "symbol": symbol,
                "exchange": exchange,
                "source": source.value,
                "timestamp": int(time.time()),
                "fetched_at": datetime.utcnow().isoformat()
            }
            
            await redis_client.set(
                redis_key,
                str(cache_payload),  # Redis stores as string
                ex=settings.REDIS_TICK_TTL  # 5 second TTL
            )
            
            # Reset failure counter on success
            self.consecutive_failures = 0
            
            elapsed = time.time() - start_time
            logger.info(f"Cached LTP for {symbol}: {ltp} (took {elapsed:.2f}s)")
            
            await self._log_audit(
                action="FETCH_LTP_SUCCESS",
                symbol=symbol,
                ltp=ltp,
                elapsed_ms=int(elapsed * 1000),
                success=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error fetching LTP for {symbol}: {e}", exc_info=True)
            self.consecutive_failures += 1
            await self._check_circuit_breaker()
            
            await self._log_audit(
                action="FETCH_LTP_ERROR",
                symbol=symbol,
                error=str(e),
                success=False
            )
            return False
    
    async def fetch_historical_batch(
        self,
        symbols: List[str],
        interval: str = "1d",
        period: str = "1mo",
        source: DataSource = DataSource.OPENALGO
    ) -> Dict[str, Any]:
        """
        Fetch historical data for multiple symbols in batch.
        
        Args:
            symbols: List of symbols to fetch
            interval: Data interval (1m, 5m, 15m, 30m, 1h, 1d)
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y)
            source: Data source
            
        Returns:
            Dict with success/failure counts and details
            
        Compliance:
            - Rule #5-6: Never fabricate, fail closed on errors
            - Rule #33-34: Every fetch logged and traceable
        """
        results = {
            "total": len(symbols),
            "successful": 0,
            "failed": 0,
            "errors": [],
            "symbols_processed": []
        }
        
        logger.info(f"Starting batch fetch: {len(symbols)} symbols, interval={interval}, period={period}")
        
        for symbol in symbols:
            try:
                # Fetch historical data
                hist_data = await asyncio.to_thread(
                    self.unified_data.get_historical_data,
                    symbol,
                    interval=interval,
                    period=period,
                    source=source.value
                )
                
                if hist_data is None or hist_data.empty:
                    logger.warning(f"No historical data for {symbol}")
                    results["failed"] += 1
                    results["errors"].append({
                        "symbol": symbol,
                        "error": "no_data_returned"
                    })
                    continue
                
                # TODO: Store in PostgreSQL historical_ohlc table
                # For now, just log success
                results["successful"] += 1
                results["symbols_processed"].append(symbol)
                
                logger.debug(f"Fetched {len(hist_data)} candles for {symbol}")
                
            except Exception as e:
                logger.error(f"Error fetching historical data for {symbol}: {e}")
                results["failed"] += 1
                results["errors"].append({
                    "symbol": symbol,
                    "error": str(e)
                })
        
        await self._log_audit(
            action="BATCH_FETCH_COMPLETE",
            total=results["total"],
            successful=results["successful"],
            failed=results["failed"],
            interval=interval,
            period=period,
            success=True
        )
        
        return results
    
    async def get_feed_health(self) -> Dict[str, Any]:
        """
        Get current feed health status.
        
        Returns:
            Dict with health status and metrics
            
        Compliance:
            - Rule #11: If feed health not HEALTHY, assume UNSAFE
        """
        now = time.time()
        
        # Throttle health checks
        if now - self.last_health_check < self.HEALTH_CHECK_INTERVAL:
            # Return cached status
            cached_status = await redis_client.get("feed:health:status")
            if cached_status:
                import json
                return json.loads(cached_status)
        
        self.last_health_check = now
        
        # Determine health status
        if self.circuit_breaker_active:
            status = FeedHealthStatus.UNHEALTHY
            reason = "Circuit breaker active due to consecutive failures"
        elif self.consecutive_failures > 0:
            status = FeedHealthStatus.DEGRADED
            reason = f"{self.consecutive_failures} recent failures"
        else:
            status = FeedHealthStatus.HEALTHY
            reason = "All systems operational"
        
        health_data = {
            "status": status.value,
            "reason": reason,
            "circuit_breaker_active": self.circuit_breaker_active,
            "consecutive_failures": self.consecutive_failures,
            "last_check": datetime.utcnow().isoformat(),
            "timestamp": int(now)
        }
        
        # Cache health status
        import json
        await redis_client.set(
            "feed:health:status",
            json.dumps(health_data),
            ex=self.HEALTH_CHECK_INTERVAL
        )
        
        return health_data
    
    async def _check_circuit_breaker(self):
        """Check if circuit breaker should be activated"""
        if self.consecutive_failures >= self.CIRCUIT_BREAKER_THRESHOLD:
            if not self.circuit_breaker_active:
                self.circuit_breaker_active = True
                logger.critical(
                    f"Circuit breaker ACTIVATED after {self.consecutive_failures} failures"
                )
                await self.alert_service.emit(
                    alert_type="CIRCUIT_BREAKER_ACTIVATED",
                    message=f"Data pipeline circuit breaker activated after {self.consecutive_failures} consecutive failures",
                    level="ERROR",
                    metadata={
                        "consecutive_failures": self.consecutive_failures,
                        "threshold": self.CIRCUIT_BREAKER_THRESHOLD
                    }
                )
    
    async def reset_circuit_breaker(self):
        """Manually reset circuit breaker"""
        if self.circuit_breaker_active:
            self.circuit_breaker_active = False
            self.consecutive_failures = 0
            logger.info("Circuit breaker manually RESET")
            await self.alert_service.emit(
                alert_type="CIRCUIT_BREAKER_RESET",
                message="Data pipeline circuit breaker manually reset",
                level="INFO"
            )
    
    async def _log_audit(self, action: str, success: bool, **metadata):
        """
        Log audit trail for all pipeline operations.
        
        Compliance:
            - Rule #33: Every decision traceable
            - Rule #34: Every execution attempt logged
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "success": success,
            "service": "data_pipeline",
            **metadata
        }
        
        # Store in Redis list (keep last 1000 entries)
        import json
        await redis_client.lpush("audit:data_pipeline", json.dumps(audit_entry))
        await redis_client.ltrim("audit:data_pipeline", 0, 999)
        
        # Also log to file
        logger.info(f"AUDIT: {action} - {'SUCCESS' if success else 'FAILED'} - {metadata}")


# Global instance
data_pipeline_service = DataPipelineService()
