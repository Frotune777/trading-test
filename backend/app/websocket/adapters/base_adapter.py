"""
Base Broker Adapter
Abstract interface for broker WebSocket adapters
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseBrokerAdapter(ABC):
    """Abstract base class for broker adapters"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connected = False
        self.subscribed_symbols = set()
    
    @abstractmethod
    async def connect(self):
        """
        Connect to broker WebSocket
        
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from broker WebSocket"""
        pass
    
    @abstractmethod
    async def subscribe(self, symbols: List[str], mode: str = "ltp"):
        """
        Subscribe to symbols
        
        Args:
            symbols: List of symbols (e.g., ["NSE:RELIANCE", "NSE:TCS"])
            mode: Subscription mode ("ltp", "quote", "full")
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, symbols: List[str]):
        """
        Unsubscribe from symbols
        
        Args:
            symbols: List of symbols to unsubscribe
        """
        pass
    
    @abstractmethod
    async def on_message(self, message: Dict[str, Any]):
        """
        Handle incoming message from broker
        
        Args:
            message: Raw message from broker
            
        Returns:
            Normalized message in standard format
        """
        pass
    
    @abstractmethod
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current quote for a symbol (REST fallback)
        
        Args:
            symbol: Symbol to get quote for
            
        Returns:
            Quote data or None if unavailable
        """
        pass
    
    def is_connected(self) -> bool:
        """Check if adapter is connected"""
        return self.connected
    
    def get_subscribed_symbols(self) -> List[str]:
        """Get list of subscribed symbols"""
        return list(self.subscribed_symbols)
    
    async def reconnect(self):
        """Reconnect to broker (with exponential backoff)"""
        logger.info(f"Reconnecting to {self.__class__.__name__}...")
        await self.disconnect()
        await self.connect()
        
        # Re-subscribe to previous symbols
        if self.subscribed_symbols:
            await self.subscribe(list(self.subscribed_symbols))
