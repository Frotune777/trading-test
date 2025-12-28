"""
Angel One WebSocket Client
Real-time market data streaming via WebSocket
"""

import asyncio
import websockets
import json
import struct
import logging
from typing import Dict, List, Callable, Optional
from datetime import datetime
import pytz

from app.brokers.angelone.angelone_auth import AngelOneAuth
from app.brokers.angelone.angelone_models import (
    AngelOneMarketData,
    ExchangeType,
    SubscriptionMode,
    SymbolToken
)

logger = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')


class AngelOneWebSocket:
    """Angel One WebSocket client for real-time market data"""
    
    def __init__(self, auth: AngelOneAuth, ws_url: str):
        """
        Initialize WebSocket client
        
        Args:
            auth: Angel One authentication handler
            ws_url: WebSocket URL
        """
        self.auth = auth
        self.ws_url = ws_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.subscriptions: Dict[str, SymbolToken] = {}
        self.message_handlers: List[Callable] = []
        self._running = False
    
    async def connect(self) -> bool:
        """
        Connect to Angel One WebSocket
        
        Returns:
            True if connection successful
        """
        try:
            # Ensure authenticated
            if not await self.auth.ensure_authenticated():
                logger.error("Authentication failed")
                return False
            
            # Connect to WebSocket
            logger.info(f"Connecting to Angel One WebSocket: {self.ws_url}")
            self.ws = await websockets.connect(self.ws_url)
            
            # Send authentication message
            auth_message = {
                "action": 1,  # Login action
                "params": {
                    "jwtToken": self.auth.jwt_token,
                    "apiKey": self.auth.api_key,
                    "clientCode": self.auth.client_id,
                    "feedToken": self.auth.feed_token
                }
            }
            
            await self.ws.send(json.dumps(auth_message))
            
            # Wait for authentication response
            response = await self.ws.recv()
            logger.info(f"Auth response: {response}")
            
            self.is_connected = True
            self._running = True
            
            # Start message listener
            asyncio.create_task(self._message_listener())
            
            logger.info("Connected to Angel One WebSocket")
            return True
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        self._running = False
        
        if self.ws:
            await self.ws.close()
            self.ws = None
        
        self.is_connected = False
        logger.info("Disconnected from Angel One WebSocket")
    
    async def subscribe(
        self,
        symbols: List[SymbolToken],
        mode: SubscriptionMode = SubscriptionMode.LTP
    ) -> bool:
        """
        Subscribe to market data
        
        Args:
            symbols: List of symbol tokens
            mode: Subscription mode (LTP, QUOTE, SNAP_QUOTE)
            
        Returns:
            True if subscription successful
        """
        try:
            if not self.is_connected:
                logger.error("Not connected to WebSocket")
                return False
            
            # Group symbols by exchange
            exchange_groups: Dict[int, List[str]] = {}
            for symbol in symbols:
                if symbol.exchange_type not in exchange_groups:
                    exchange_groups[symbol.exchange_type] = []
                exchange_groups[symbol.exchange_type].append(symbol.token)
                
                # Store subscription
                self.subscriptions[symbol.token] = symbol
            
            # Create subscription message
            token_list = [
                {
                    "exchangeType": exchange_type,
                    "tokens": tokens
                }
                for exchange_type, tokens in exchange_groups.items()
            ]
            
            subscribe_message = {
                "action": 1,  # Subscribe action
                "params": {
                    "mode": mode.value,
                    "tokenList": token_list
                }
            }
            
            await self.ws.send(json.dumps(subscribe_message))
            
            logger.info(f"Subscribed to {len(symbols)} symbols in mode {mode.name}")
            return True
            
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            return False
    
    async def unsubscribe(self, symbols: List[SymbolToken]) -> bool:
        """
        Unsubscribe from market data
        
        Args:
            symbols: List of symbol tokens
            
        Returns:
            True if unsubscription successful
        """
        try:
            if not self.is_connected:
                return False
            
            # Group symbols by exchange
            exchange_groups: Dict[int, List[str]] = {}
            for symbol in symbols:
                if symbol.exchange_type not in exchange_groups:
                    exchange_groups[symbol.exchange_type] = []
                exchange_groups[symbol.exchange_type].append(symbol.token)
                
                # Remove from subscriptions
                self.subscriptions.pop(symbol.token, None)
            
            # Create unsubscribe message
            token_list = [
                {
                    "exchangeType": exchange_type,
                    "tokens": tokens
                }
                for exchange_type, tokens in exchange_groups.items()
            ]
            
            unsubscribe_message = {
                "action": 0,  # Unsubscribe action
                "params": {
                    "mode": 1,
                    "tokenList": token_list
                }
            }
            
            await self.ws.send(json.dumps(unsubscribe_message))
            
            logger.info(f"Unsubscribed from {len(symbols)} symbols")
            return True
            
        except Exception as e:
            logger.error(f"Unsubscription error: {e}")
            return False
    
    def add_message_handler(self, handler: Callable):
        """
        Add a message handler callback
        
        Args:
            handler: Callback function to handle market data
        """
        self.message_handlers.append(handler)
    
    async def _message_listener(self):
        """Listen for incoming WebSocket messages"""
        try:
            while self._running and self.ws:
                try:
                    message = await self.ws.recv()
                    
                    # Angel One sends binary data
                    if isinstance(message, bytes):
                        await self._parse_binary_message(message)
                    else:
                        # JSON message (heartbeat, etc.)
                        logger.debug(f"JSON message: {message}")
                        
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection closed")
                    self.is_connected = False
                    await self._reconnect()
                    break
                    
        except Exception as e:
            logger.error(f"Message listener error: {e}")
    
    async def _parse_binary_message(self, data: bytes):
        """
        Parse binary market data message
        
        Args:
            data: Binary message data
        """
        try:
            # Angel One binary format parsing
            # This is a simplified version - actual format may vary
            offset = 0
            
            while offset < len(data):
                # Read subscription mode (1 byte)
                subscription_mode = struct.unpack_from('B', data, offset)[0]
                offset += 1
                
                # Read exchange type (1 byte)
                exchange_type = struct.unpack_from('B', data, offset)[0]
                offset += 1
                
                # Read token (25 bytes, null-terminated string)
                token_bytes = data[offset:offset+25]
                token = token_bytes.decode('utf-8').rstrip('\x00')
                offset += 25
                
                # Read sequence number (8 bytes)
                sequence_number = struct.unpack_from('Q', data, offset)[0]
                offset += 8
                
                # Read exchange timestamp (8 bytes)
                exchange_timestamp = struct.unpack_from('Q', data, offset)[0]
                offset += 8
                
                # Read LTP (8 bytes)
                ltp = struct.unpack_from('Q', data, offset)[0]
                offset += 8
                
                # Create market data object
                market_data = AngelOneMarketData(
                    exchange_type=exchange_type,
                    token=token,
                    sequence_number=sequence_number,
                    exchange_timestamp=exchange_timestamp,
                    last_traded_price=ltp,
                    subscription_mode=subscription_mode
                )
                
                # Call handlers
                for handler in self.message_handlers:
                    await handler(market_data)
                    
        except Exception as e:
            logger.error(f"Binary message parsing error: {e}")
    
    async def _reconnect(self):
        """Attempt to reconnect to WebSocket"""
        logger.info("Attempting to reconnect...")
        
        max_attempts = 5
        attempt = 0
        
        while attempt < max_attempts and self._running:
            attempt += 1
            logger.info(f"Reconnection attempt {attempt}/{max_attempts}")
            
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            if await self.connect():
                # Re-subscribe to previous symbols
                if self.subscriptions:
                    symbols = list(self.subscriptions.values())
                    await self.subscribe(symbols)
                logger.info("Reconnection successful")
                return
        
        logger.error("Reconnection failed after maximum attempts")
