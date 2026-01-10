# app/services/alert_service.py

import json
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from app.core.redis import redis_client
from app.database.db_manager import DatabaseManager

if TYPE_CHECKING:
    from app.core.trade_intent import TradeIntent

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
        channels: Optional[List[str]] = None,
        intent: Optional['TradeIntent'] = None
    ):
        """
        Emit a system alert through multiple channels.
        
        Args:
            intent: Optional TradeIntent context (v1.1)
        """
        # Check throttling
        if not self._should_send_alert(alert_type, symbol):
            logger.debug(f"Alert throttled: {alert_type} for {symbol}")
            return
        
        # Serialize intent if provided
        intent_data = None
        if intent:
            try:
                # Basic serialization - ideal would be proper dict conversion method
                intent_data = {
                    "bias": intent.directional_bias.value,
                    "score": intent.conviction_score,
                    "pillars": [p.name for p in intent.pillar_contributions],
                    "valid": intent.is_analysis_valid
                }
            except Exception as e:
                logger.warning(f"Failed to serialize intent for alert: {e}")

        alert_payload = {
            "type": alert_type,
            "level": level,
            "symbol": symbol,
            "message": message,
            "metadata": metadata or {},
            "intent": intent_data,
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
        
        # 3. Send via Telegram (via OpenAlgo)
        if "telegram" in target_channels:
            try:
                from app.core.openalgo_bridge import openalgo_bridge
                
                # Format message for Telegram
                tg_message = f"🚨 *{alert_type.replace('_', ' ').title()}* [{level}]\n"
                tg_message += f"{message}\n"
                if symbol:
                    tg_message += f"Symbol: `{symbol}`\n"
                if metadata:
                    tg_message += f"Context: {json.dumps(metadata, default=str)}"
                
                # Delegate to OpenAlgo
                # If a specific user ID was passed in metadata (custom convention), use it
                telegram_id = metadata.get('telegram_id') if metadata else None
                openalgo_bridge.send_alert(tg_message, telegram_id)
                
            except Exception as e:
                logger.error(f"Failed to send OpenAlgo Telegram alert: {e}")
        
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
