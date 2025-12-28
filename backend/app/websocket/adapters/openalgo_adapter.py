"""
OpenAlgo Broker Adapter
Adapter for OpenAlgo WebSocket/REST API
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import aiohttp

from .base_adapter import BaseBrokerAdapter

logger = logging.getLogger(__name__)

class OpenAlgoAdapter(BaseBrokerAdapter):
    """OpenAlgo broker adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:5000")
        self.api_key = config.get("api_key")
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def connect(self):
        """Connect to OpenAlgo (REST-based, no persistent WebSocket yet)"""
        self.session = aiohttp.ClientSession()
        
        # Verify connection with health check
        try:
            async with self.session.get(f"{self.base_url}/api/v1/health") as resp:
                if resp.status == 200:
                    self.connected = True
                    logger.info("✅ Connected to OpenAlgo")
                else:
                    raise ConnectionError(f"OpenAlgo health check failed: {resp.status}")
        except Exception as e:
            logger.error(f"Failed to connect to OpenAlgo: {e}")
            raise ConnectionError(f"OpenAlgo connection failed: {e}")
    
    async def disconnect(self):
        """Disconnect from OpenAlgo"""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
        logger.info("Disconnected from OpenAlgo")
    
    async def subscribe(self, symbols: List[str], mode: str = "ltp"):
        """
        Subscribe to symbols (OpenAlgo uses REST polling, not WebSocket)
        
        Note: OpenAlgo doesn't have native WebSocket streaming yet.
        We'll poll the REST API at regular intervals.
        """
        self.subscribed_symbols.update(symbols)
        logger.info(f"Subscribed to {len(symbols)} symbols in {mode} mode (REST polling)")
        
        # Start polling task for these symbols
        asyncio.create_task(self._poll_symbols(symbols, mode))
    
    async def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from symbols"""
        self.subscribed_symbols.difference_update(symbols)
        logger.info(f"Unsubscribed from {len(symbols)} symbols")
    
    async def _poll_symbols(self, symbols: List[str], mode: str, interval: float = 1.0):
        """
        Poll symbols at regular intervals
        
        Args:
            symbols: Symbols to poll
            mode: Data mode (ltp, quote, full)
            interval: Polling interval in seconds
        """
        while all(s in self.subscribed_symbols for s in symbols):
            for symbol in symbols:
                if symbol not in self.subscribed_symbols:
                    continue
                
                try:
                    quote = await self.get_quote(symbol)
                    if quote:
                        await self.on_message(quote)
                except Exception as e:
                    logger.error(f"Error polling {symbol}: {e}")
            
            await asyncio.sleep(interval)
    
    async def on_message(self, message: Dict[str, Any]):
        """
        Process message from OpenAlgo
        
        OpenAlgo Native Format (we use this as-is):
        {
            "symbol": "NSE:RELIANCE",
            "exchange": "NSE",
            "ltp": 2500.50,
            "open": 2480.00,
            "high": 2510.00,
            "low": 2475.00,
            "close": 2495.00,
            "volume": 1000000,
            "oi": 50000,  # Open Interest (for F&O)
            "timestamp": "2024-01-01T10:00:00+05:30"
        }
        
        We adopt OpenAlgo's format as our standard.
        """
        # Use OpenAlgo format as-is (no conversion needed)
        return message
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current quote from OpenAlgo REST API
        
        Args:
            symbol: Symbol to get quote for (e.g., "NSE:RELIANCE")
        """
        if not self.session or not self.connected:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with self.session.get(
                f"{self.base_url}/api/v1/quotes",
                params={"symbol": symbol},
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data
                else:
                    logger.warning(f"Failed to get quote for {symbol}: {resp.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return None
    
    async def get_ltp(self, symbol: str) -> Optional[float]:
        """Get Last Traded Price for a symbol"""
        quote = await self.get_quote(symbol)
        if quote:
            return quote.get("ltp")
        return None
