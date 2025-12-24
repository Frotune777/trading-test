# app/services/alert_service.py

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.redis import redis_client
from app.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class AlertService:
    """
    Centralized alerting engine.
    Broadcasts alerts via Redis Pub/Sub and persists them to DB.
    """
    CHANNEL = "system:alerts"
    
    def __init__(self, db_path: str = "stock_data.db"):
        self.db = DatabaseManager(db_path)

    async def emit(self, alert_type: str, message: str, level: str = "INFO", 
                   symbol: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Emit a system alert.
        """
        alert_payload = {
            "type": alert_type,
            "level": level,
            "symbol": symbol,
            "message": message,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        
        # 1. Persist to Database
        try:
            self.db.save_alert(alert_payload)
        except Exception as e:
            logger.error(f"Failed to persist alert in DB: {e}")
            
        # 2. Broadcast via Redis Pub/Sub
        try:
            await redis_client.publish(self.CHANNEL, json.dumps(alert_payload))
            logger.info(f"📢 ALERT [{level}] {alert_type}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish alert to Redis: {e}")

    def get_latest_alerts(self, limit: int = 50) -> List[Dict]:
        """Fetch alerts from audit trail."""
        return self.db.get_recent_alerts(limit)
