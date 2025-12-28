"""
Feed Health Monitor
Monitors market data feed health and triggers circuit breaker
"""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class FeedStatus(Enum):
    """Feed health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    STALE = "stale"
    DISCONNECTED = "disconnected"

class FeedHealthMonitor:
    """Monitors feed health and triggers alerts"""
    
    def __init__(self, stale_threshold_seconds: int = 5):
        self.stale_threshold = timedelta(seconds=stale_threshold_seconds)
        
        # symbol -> last message timestamp
        self.last_message_time: Dict[str, datetime] = {}
        
        # symbol -> message count
        self.message_count: Dict[str, int] = {}
        
        # symbol -> current status
        self.feed_status: Dict[str, FeedStatus] = {}
        
        # Global feed status
        self.global_status = FeedStatus.DISCONNECTED
        
        # Monitoring task
        self.monitor_task: Optional[asyncio.Task] = None
    
    def start(self):
        """Start monitoring"""
        if not self.monitor_task:
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info("✅ Feed health monitor started")
    
    def stop(self):
        """Stop monitoring"""
        if self.monitor_task:
            self.monitor_task.cancel()
            self.monitor_task = None
            logger.info("Feed health monitor stopped")
    
    def record_message(self, symbol: str):
        """Record a message received for a symbol"""
        now = datetime.utcnow()
        self.last_message_time[symbol] = now
        self.message_count[symbol] = self.message_count.get(symbol, 0) + 1
        
        # Update status to healthy
        old_status = self.feed_status.get(symbol)
        self.feed_status[symbol] = FeedStatus.HEALTHY
        
        # Log status change
        if old_status and old_status != FeedStatus.HEALTHY:
            logger.info(f"Feed recovered for {symbol}: {old_status.value} → HEALTHY")
    
    def get_feed_status(self, symbol: str) -> FeedStatus:
        """Get current feed status for a symbol"""
        return self.feed_status.get(symbol, FeedStatus.DISCONNECTED)
    
    def get_global_status(self) -> FeedStatus:
        """Get overall feed health status"""
        if not self.feed_status:
            return FeedStatus.DISCONNECTED
        
        # If any feed is stale, global is degraded
        statuses = list(self.feed_status.values())
        if FeedStatus.STALE in statuses:
            return FeedStatus.DEGRADED
        if FeedStatus.DISCONNECTED in statuses:
            return FeedStatus.DEGRADED
        
        return FeedStatus.HEALTHY
    
    def get_time_since_last_message(self, symbol: str) -> Optional[timedelta]:
        """Get time since last message for a symbol"""
        if symbol not in self.last_message_time:
            return None
        
        return datetime.utcnow() - self.last_message_time[symbol]
    
    def is_feed_healthy(self, symbol: str) -> bool:
        """Check if feed is healthy for a symbol"""
        status = self.get_feed_status(symbol)
        return status == FeedStatus.HEALTHY
    
    def get_stats(self) -> Dict:
        """Get feed health statistics"""
        now = datetime.utcnow()
        
        stats = {
            "global_status": self.global_status.value,
            "monitored_symbols": len(self.feed_status),
            "symbols": {}
        }
        
        for symbol in self.feed_status.keys():
            time_since = self.get_time_since_last_message(symbol)
            stats["symbols"][symbol] = {
                "status": self.feed_status[symbol].value,
                "message_count": self.message_count.get(symbol, 0),
                "seconds_since_last_message": time_since.total_seconds() if time_since else None
            }
        
        return stats
    
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await self._check_feed_health()
                await asyncio.sleep(1)  # Check every second
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in feed health monitor: {e}")
    
    async def _check_feed_health(self):
        """Check feed health for all symbols"""
        now = datetime.utcnow()
        
        for symbol in list(self.last_message_time.keys()):
            time_since = now - self.last_message_time[symbol]
            old_status = self.feed_status.get(symbol)
            
            # Determine new status
            if time_since > self.stale_threshold:
                new_status = FeedStatus.STALE
            else:
                new_status = FeedStatus.HEALTHY
            
            # Update status
            self.feed_status[symbol] = new_status
            
            # Log status changes
            if old_status and old_status != new_status:
                logger.warning(
                    f"Feed status changed for {symbol}: {old_status.value} → {new_status.value} "
                    f"(last message: {time_since.total_seconds():.1f}s ago)"
                )
                
                # Trigger alert for stale feeds
                if new_status == FeedStatus.STALE:
                    await self._trigger_alert(symbol, time_since)
        
        # Update global status
        self.global_status = self.get_global_status()
    
    async def _trigger_alert(self, symbol: str, time_since: timedelta):
        """Trigger alert for stale feed"""
        logger.error(
            f"⚠️  FEED ALERT: {symbol} feed is STALE "
            f"(last message: {time_since.total_seconds():.1f}s ago)"
        )
        
        # TODO: Send alert to monitoring system
        # TODO: Trigger circuit breaker if needed
