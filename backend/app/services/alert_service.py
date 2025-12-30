# app/services/alert_service.py

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.core.redis import redis_client
from app.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class AlertService:
    """
    Enhanced centralized alerting engine.
    Supports multiple channels: Redis Pub/Sub, Telegram, WebSocket, Database
    """
    CHANNEL = "system:alerts"
    
    # Alert throttling: max alerts per symbol per time window
    THROTTLE_WINDOW_SECONDS = 60
    MAX_ALERTS_PER_WINDOW = 5
    
    def __init__(self, db_path: str = "stock_data.db"):
        self.db = DatabaseManager(db_path)
        self._telegram_bot = None
        self._alert_counts: Dict[str, List[datetime]] = {}  # For throttling

    async def emit(
        self,
        alert_type: str,
        message: str,
        level: str = "INFO",
        symbol: Optional[str] = None,
        metadata: Optional[Dict] = None,
        channels: Optional[List[str]] = None
    ):
        """
        Emit a system alert through multiple channels.
        
        Args:
            alert_type: Type of alert (e.g., "RISK_LIMIT_BREACH", "EXECUTION_BLOCKED")
            message: Alert message
            level: Severity level (INFO, WARNING, ERROR, CRITICAL)
            symbol: Optional stock symbol
            metadata: Additional metadata
            channels: List of channels to use (default: all enabled)
        """
        # Check throttling
        if not self._should_send_alert(alert_type, symbol):
            logger.debug(f"Alert throttled: {alert_type} for {symbol}")
            return
        
        alert_payload = {
            "type": alert_type,
            "level": level,
            "symbol": symbol,
            "message": message,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Default channels: Redis, Database, and Telegram (if configured)
        target_channels = channels or ["redis", "database", "telegram"]
        
        # 1. Persist to Database
        if "database" in target_channels:
            try:
                self.db.save_alert(alert_payload)
            except Exception as e:
                logger.error(f"Failed to persist alert in DB: {e}")
        
        # 2. Broadcast via Redis Pub/Sub (for WebSocket consumption)
        if "redis" in target_channels:
            try:
                await redis_client.publish(self.CHANNEL, json.dumps(alert_payload))
                logger.info(f"📢 ALERT [{level}] {alert_type}: {message}")
            except Exception as e:
                logger.error(f"Failed to publish alert to Redis: {e}")
        
        # 3. Send via Telegram (if enabled)
        if "telegram" in target_channels:
            try:
                telegram_bot = self._get_telegram_bot()
                if telegram_bot and telegram_bot.enabled:
                    await telegram_bot.send_alert(
                        message=message,
                        level=level,
                        title=alert_type.replace("_", " ").title(),
                        metadata=metadata
                    )
            except Exception as e:
                logger.error(f"Failed to send Telegram alert: {e}")
        
        # Record alert for throttling
        self._record_alert(alert_type, symbol)

    def _should_send_alert(self, alert_type: str, symbol: Optional[str]) -> bool:
        """Check if alert should be sent based on throttling rules."""
        key = f"{alert_type}:{symbol or 'global'}"
        now = datetime.now()
        
        # Clean old timestamps
        if key in self._alert_counts:
            cutoff = now - timedelta(seconds=self.THROTTLE_WINDOW_SECONDS)
            self._alert_counts[key] = [
                ts for ts in self._alert_counts[key] if ts > cutoff
            ]
        
        # Check count
        count = len(self._alert_counts.get(key, []))
        return count < self.MAX_ALERTS_PER_WINDOW
    
    def _record_alert(self, alert_type: str, symbol: Optional[str]):
        """Record alert timestamp for throttling."""
        key = f"{alert_type}:{symbol or 'global'}"
        if key not in self._alert_counts:
            self._alert_counts[key] = []
        self._alert_counts[key].append(datetime.now())
    
    def _get_telegram_bot(self):
        """Lazy load Telegram bot."""
        if self._telegram_bot is None:
            try:
                from app.services.telegram_bot import get_telegram_bot
                self._telegram_bot = get_telegram_bot()
            except Exception as e:
                logger.warning(f"Failed to initialize Telegram bot: {e}")
                self._telegram_bot = None
        return self._telegram_bot

    def get_latest_alerts(self, limit: int = 50) -> List[Dict]:
        """Fetch alerts from audit trail."""
        return self.db.get_recent_alerts(limit)
    
    async def send_risk_alert(
        self,
        alert_type: str,
        symbol: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Convenience method for risk alerts."""
        await self.emit(
            alert_type=f"RISK_{alert_type}",
            message=f"Risk limit breached for {symbol}: {reason}",
            level="WARNING",
            symbol=symbol,
            metadata=details
        )
    
    async def send_execution_alert(
        self,
        symbol: str,
        action: str,
        status: str,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Convenience method for execution alerts."""
        level = "INFO" if status == "SUCCESS" else "WARNING"
        message = f"{action} order for {symbol}: {status}"
        if reason:
            message += f" - {reason}"
        
        await self.emit(
            alert_type=f"EXECUTION_{status}",
            message=message,
            level=level,
            symbol=symbol,
            metadata=details
        )
