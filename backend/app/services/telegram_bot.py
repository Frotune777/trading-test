"""
Telegram Bot Service for Trading Alerts
Sends formatted alerts to Telegram users/channels
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

from app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramAlertBot:
    """
    Telegram bot for sending trading alerts.
    
    Features:
    - Send formatted alerts with severity indicators
    - Support for multiple chat IDs (users/channels)
    - Message throttling to prevent spam
    - Emoji indicators for alert levels
    """
    
    # Emoji indicators for alert levels
    LEVEL_EMOJI = {
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🚨"
    }
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram bot.
        
        Args:
            bot_token: Telegram bot token (from settings if not provided)
            chat_id: Default chat ID to send messages to
        """
        self.bot_token = bot_token or getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.chat_id = chat_id or getattr(settings, 'TELEGRAM_CHAT_ID', None)
        self.bot: Optional[Bot] = None
        self.enabled = False
        
        if self.bot_token:
            try:
                self.bot = Bot(token=self.bot_token)
                self.enabled = True
                logger.info("✅ Telegram bot initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.enabled = False
        else:
            logger.warning("Telegram bot token not configured - alerts will not be sent")
    
    async def send_alert(
        self,
        message: str,
        level: str = "INFO",
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        chat_id: Optional[str] = None
    ) -> bool:
        """
        Send alert message to Telegram.
        
        Args:
            message: Alert message
            level: Alert severity (INFO, WARNING, ERROR, CRITICAL)
            title: Optional alert title
            metadata: Optional metadata to include
            chat_id: Override default chat ID
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled or not self.bot:
            logger.debug("Telegram bot not enabled - skipping alert")
            return False
        
        target_chat_id = chat_id or self.chat_id
        if not target_chat_id:
            logger.warning("No Telegram chat ID configured")
            return False
        
        try:
            # Format message
            emoji = self.LEVEL_EMOJI.get(level.upper(), "📢")
            formatted_message = self._format_message(emoji, level, title, message, metadata)
            
            # Send message
            await self.bot.send_message(
                chat_id=target_chat_id,
                text=formatted_message,
                parse_mode='HTML'
            )
            
            logger.info(f"📤 Telegram alert sent: [{level}] {title or message[:50]}")
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram alert: {e}", exc_info=True)
            return False
    
    def _format_message(
        self,
        emoji: str,
        level: str,
        title: Optional[str],
        message: str,
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Format alert message for Telegram."""
        lines = []
        
        # Header with emoji and level
        lines.append(f"{emoji} <b>{level}</b>")
        
        # Title if provided
        if title:
            lines.append(f"<b>{title}</b>")
        
        # Message
        lines.append(f"\n{message}")
        
        # Metadata if provided
        if metadata:
            lines.append("\n<i>Details:</i>")
            for key, value in metadata.items():
                lines.append(f"• {key}: {value}")
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
        lines.append(f"\n<i>{timestamp}</i>")
        
        return "\n".join(lines)
    
    async def send_risk_alert(
        self,
        alert_type: str,
        symbol: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send risk-related alert (convenience method).
        
        Args:
            alert_type: Type of risk alert (e.g., "DAILY_LOSS_LIMIT", "KILL_SWITCH")
            symbol: Stock symbol
            reason: Block reason
            details: Additional details
        """
        title = f"🛡️ Risk Alert: {alert_type}"
        message = f"Symbol: <b>{symbol}</b>\nReason: {reason}"
        
        return await self.send_alert(
            message=message,
            level="WARNING",
            title=title,
            metadata=details
        )
    
    async def send_execution_alert(
        self,
        symbol: str,
        action: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send execution-related alert (convenience method).
        
        Args:
            symbol: Stock symbol
            action: BUY/SELL
            status: SUCCESS/BLOCKED/FAILED
            details: Additional details
        """
        emoji_map = {
            "SUCCESS": "✅",
            "BLOCKED": "🚫",
            "FAILED": "❌"
        }
        
        emoji = emoji_map.get(status, "📊")
        title = f"{emoji} Trade {status}: {symbol}"
        message = f"Action: <b>{action}</b>\nStatus: {status}"
        
        level = "INFO" if status == "SUCCESS" else "WARNING"
        
        return await self.send_alert(
            message=message,
            level=level,
            title=title,
            metadata=details
        )
    
    async def test_connection(self) -> bool:
        """
        Test Telegram bot connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.enabled or not self.bot:
            return False
        
        try:
            me = await self.bot.get_me()
            logger.info(f"✅ Telegram bot connected: @{me.username}")
            return True
        except Exception as e:
            logger.error(f"Telegram bot connection test failed: {e}")
            return False


# Global singleton instance
telegram_bot: Optional[TelegramAlertBot] = None


def get_telegram_bot() -> TelegramAlertBot:
    """Get or create global Telegram bot instance."""
    global telegram_bot
    if telegram_bot is None:
        telegram_bot = TelegramAlertBot()
    return telegram_bot
