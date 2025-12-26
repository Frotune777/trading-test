"""
Feed Health Monitor
Tracks data feed health and provides real-time status.
Complies with Rule #11 (if feed health not HEALTHY, assume UNSAFE).
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import time

from app.core.redis import redis_client
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)


class FeedStatus(Enum):
    """Feed health status"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


class FeedHealthMonitor:
    """
    Monitors data feed health in real-time.
    
    Compliance:
        - Rule #11: If feed health not HEALTHY, assume UNSAFE
        - Rule #40: UI must show feed health clearly
    """
    
    def __init__(self):
        self.alert_service = AlertService()
        self.check_interval = 10  # seconds
        self.is_running = False
        self._monitor_task = None
    
    async def start_monitoring(self):
        """Start the background monitoring task"""
        if self.is_running:
            logger.warning("Feed health monitor already running")
            return
        
        self.is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Feed health monitor started")
    
    async def stop_monitoring(self):
        """Stop the background monitoring task"""
        self.is_running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Feed health monitor stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                health_data = await self.check_health()
                await self._store_health_metrics(health_data)
                
                # Alert on status changes
                await self._check_status_change(health_data)
                
            except Exception as e:
                logger.error(f"Error in feed health monitor: {e}", exc_info=True)
            
            await asyncio.sleep(self.check_interval)
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check current feed health.
        
        Returns:
            Dict with health status and metrics
        """
        now = time.time()
        
        # Check OpenAlgo WebSocket status
        openalgo_status = await self._check_openalgo_status()
        
        # Check data pipeline status
        pipeline_status = await self._check_pipeline_status()
        
        # Check Redis connectivity
        redis_status = await self._check_redis_status()
        
        # Determine overall status
        overall_status = self._determine_overall_status(
            openalgo_status,
            pipeline_status,
            redis_status
        )
        
        health_data = {
            "status": overall_status.value,
            "timestamp": int(now),
            "checked_at": datetime.utcnow().isoformat(),
            "components": {
                "openalgo": openalgo_status,
                "data_pipeline": pipeline_status,
                "redis": redis_status
            },
            "metrics": {
                "active_symbols": await self._count_active_symbols(),
                "stale_symbols": await self._count_stale_symbols()
            }
        }
        
        return health_data
    
    async def _check_openalgo_status(self) -> Dict[str, Any]:
        """Check OpenAlgo WebSocket feed status"""
        try:
            # Check if OpenAlgo feed state is stored in Redis
            feed_state = await redis_client.get("feed:openalgo:state")
            
            if not feed_state:
                return {
                    "status": "UNKNOWN",
                    "healthy": False,
                    "message": "No feed state available"
                }
            
            # Parse feed state
            import json
            state_data = json.loads(feed_state) if isinstance(feed_state, str) else feed_state
            
            is_healthy = state_data.get("feed_state") == "HEALTHY"
            
            return {
                "status": state_data.get("feed_state", "UNKNOWN"),
                "healthy": is_healthy,
                "connected": state_data.get("connected", False),
                "active_symbols": len(state_data.get("active_symbols", [])),
                "message": "OpenAlgo feed operational" if is_healthy else "OpenAlgo feed issues detected"
            }
            
        except Exception as e:
            logger.debug(f"OpenAlgo status check skipped (Redis unavailable): {e}")
            return {
                "status": "ERROR",
                "healthy": False,
                "message": f"Error: {str(e)}"
            }
    
    async def _check_pipeline_status(self) -> Dict[str, Any]:
        """Check data pipeline status"""
        try:
            # Check if circuit breaker is active
            pipeline_health = await redis_client.get("feed:health:status")
            
            if not pipeline_health:
                return {
                    "status": "UNKNOWN",
                    "healthy": False,
                    "message": "No pipeline health data"
                }
            
            import json
            health_data = json.loads(pipeline_health) if isinstance(pipeline_health, str) else pipeline_health
            
            is_healthy = health_data.get("status") == "HEALTHY"
            circuit_breaker = health_data.get("circuit_breaker_active", False)
            
            return {
                "status": health_data.get("status", "UNKNOWN"),
                "healthy": is_healthy and not circuit_breaker,
                "circuit_breaker_active": circuit_breaker,
                "consecutive_failures": health_data.get("consecutive_failures", 0),
                "message": "Pipeline operational" if is_healthy else health_data.get("reason", "Unknown issue")
            }
            
        except Exception as e:
            logger.debug(f"Pipeline status check skipped (Redis unavailable): {e}")
            return {
                "status": "ERROR",
                "healthy": False,
                "message": f"Error: {str(e)}"
            }
    
    async def _check_redis_status(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            # Simple ping test
            await redis_client.ping()
            
            return {
                "status": "HEALTHY",
                "healthy": True,
                "message": "Redis connected"
            }
            
        except Exception as e:
            # Redis is optional - don't spam logs
            if not hasattr(self, '_redis_warning_logged'):
                logger.warning(f"Redis unavailable (optional service): {e}")
                self._redis_warning_logged = True
            
            return {
                "status": "UNAVAILABLE",
                "healthy": False,
                "message": "Redis not available (caching disabled)"
            }
    
    def _determine_overall_status(
        self,
        openalgo: Dict,
        pipeline: Dict,
        redis: Dict
    ) -> FeedStatus:
        """
        Determine overall feed health status.
        
        Rule #11: If feed health not HEALTHY, assume UNSAFE
        Note: Redis is optional - system can operate without it
        """
        # Redis is optional - don't fail if it's down
        # Just log a warning (already logged in _check_redis_status)
        
        # If pipeline circuit breaker is active, UNHEALTHY
        if pipeline.get("circuit_breaker_active", False):
            return FeedStatus.UNHEALTHY
        
        # Count healthy components (excluding Redis)
        healthy_count = sum([
            openalgo.get("healthy", False),
            pipeline.get("healthy", False)
        ])
        
        # Determine status based on critical components only
        if healthy_count == 2:
            return FeedStatus.HEALTHY
        elif healthy_count == 1:
            return FeedStatus.DEGRADED
        else:
            return FeedStatus.UNHEALTHY
    
    async def _count_active_symbols(self) -> int:
        """Count symbols with fresh LTP data (<5s)"""
        try:
            # Get all LTP keys
            keys = await redis_client.keys("ltp:*")
            
            if not keys:
                return 0
            
            now = time.time()
            active_count = 0
            
            for key in keys:
                ttl = await redis_client.ttl(key)
                # If TTL exists and > 0, it's active
                if ttl > 0:
                    active_count += 1
            
            return active_count
            
        except Exception:
            # Redis unavailable - return 0 silently
            return 0
    
    async def _count_stale_symbols(self) -> int:
        """Count symbols with stale data (>5s or expired)"""
        try:
            # Get all market:ltp keys (from OpenAlgo bridge)
            keys = await redis_client.keys("market:ltp:*")
            
            if not keys:
                return 0
            
            stale_count = 0
            
            for key in keys:
                ttl = await redis_client.ttl(key)
                # If TTL is -1 (no expiry) or -2 (expired), it's stale
                if ttl < 0:
                    stale_count += 1
            
            return stale_count
            
        except Exception:
            # Redis unavailable - return 0 silently
            return 0
    
    async def _store_health_metrics(self, health_data: Dict):
        """Store health metrics in Redis for historical tracking"""
        try:
            import json
            
            # Store current health
            await redis_client.set(
                "feed:health:current",
                json.dumps(health_data),
                ex=60  # 1 minute expiry
            )
            
            # Store in time-series (keep last 100 checks)
            await redis_client.lpush(
                "feed:health:history",
                json.dumps(health_data)
            )
            await redis_client.ltrim("feed:health:history", 0, 99)
            
        except Exception:
            # Redis unavailable - skip storage silently
            pass
    
    async def _check_status_change(self, health_data: Dict):
        """Alert on status changes"""
        try:
            current_status = health_data["status"]
            
            # Get previous status
            prev_status = await redis_client.get("feed:health:previous_status")
            
            if prev_status and prev_status != current_status:
                # Status changed
                await self.alert_service.emit(
                    alert_type=f"FEED_STATUS_CHANGE",
                    message=f"Feed health changed: {prev_status} → {current_status}",
                    level="WARNING" if current_status != "HEALTHY" else "INFO",
                    metadata={
                        "previous_status": prev_status,
                        "current_status": current_status,
                        "components": health_data["components"]
                    }
                )
            
            # Store current as previous
            await redis_client.set("feed:health:previous_status", current_status)
            
        except Exception:
            # Redis unavailable - skip status change tracking silently
            pass
    
    async def get_health_history(self, limit: int = 20) -> List[Dict]:
        """Get historical health data"""
        try:
            import json
            history = await redis_client.lrange("feed:health:history", 0, limit - 1)
            return [json.loads(item) for item in history]
        except Exception as e:
            logger.error(f"Error getting health history: {e}")
            return []


# Global instance
feed_health_monitor = FeedHealthMonitor()
