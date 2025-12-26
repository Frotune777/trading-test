"""
Multi-Broker WebSocket Connection Manager
Manages WebSocket connections to multiple brokers simultaneously.
"""

import asyncio
import logging
from typing import Dict, Optional, Callable, Any
from datetime import datetime

from app.brokers.base_adapter import BrokerType, BrokerAdapter
from app.core.redis import redis_client

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Multi-Broker WebSocket Manager
    
    Features:
        - Manage WebSocket connections to multiple brokers
        - Auto-reconnection on disconnect
        - Tick aggregation from all brokers
        - Subscribe/unsubscribe to symbols
        - Broadcast ticks to subscribers
    
    Usage:
        ws_manager = WebSocketManager()
        await ws_manager.add_broker(zerodha_adapter)
        await ws_manager.subscribe("RELIANCE", "NSE")
        await ws_manager.start()
    """
    
    def __init__(self):
        self.brokers: Dict[BrokerType, BrokerAdapter] = {}
        self.connections: Dict[BrokerType, Any] = {}
        self.subscriptions: Dict[str, set] = {}  # symbol -> set of brokers
        self.tick_callbacks: list[Callable] = []
        self._running = False
        
        logger.info("WebSocketManager initialized")
    
    def add_broker(self, broker: BrokerAdapter):
        """Register a broker for WebSocket streaming"""
        self.brokers[broker.broker_type] = broker
        logger.info(f"Added broker to WebSocket manager: {broker.broker_name}")
    
    def add_tick_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Add callback to receive tick updates.
        
        Args:
            callback: Function to call with tick data
        """
        self.tick_callbacks.append(callback)
        logger.info(f"Added tick callback: {callback.__name__}")
    
    async def subscribe(self, symbol: str, exchange: str = "NSE", brokers: Optional[list[BrokerType]] = None):
        """
        Subscribe to symbol across specified brokers.
        
        Args:
            symbol: Stock symbol
            exchange: Exchange name
            brokers: List of brokers to subscribe on (None = all)
        """
        key = f"{exchange}:{symbol}"
        
        if key not in self.subscriptions:
            self.subscriptions[key] = set()
        
        # Subscribe on specified brokers or all
        target_brokers = brokers or list(self.brokers.keys())
        
        for broker_type in target_brokers:
            if broker_type in self.brokers:
                self.subscriptions[key].add(broker_type)
                logger.info(f"Subscribed to {symbol} on {broker_type.value}")
    
    async def unsubscribe(self, symbol: str, exchange: str = "NSE", brokers: Optional[list[BrokerType]] = None):
        """Unsubscribe from symbol"""
        key = f"{exchange}:{symbol}"
        
        if key not in self.subscriptions:
            return
        
        target_brokers = brokers or list(self.brokers.keys())
        
        for broker_type in target_brokers:
            if broker_type in self.subscriptions[key]:
                self.subscriptions[key].remove(broker_type)
                logger.info(f"Unsubscribed from {symbol} on {broker_type.value}")
        
        # Remove key if no subscriptions left
        if not self.subscriptions[key]:
            del self.subscriptions[key]
    
    async def start(self):
        """Start WebSocket connections to all brokers"""
        if self._running:
            logger.warning("WebSocketManager already running")
            return
        
        self._running = True
        logger.info("Starting WebSocket connections...")
        
        # Start connection tasks for each broker
        tasks = []
        for broker_type, broker in self.brokers.items():
            task = asyncio.create_task(
                self._maintain_connection(broker_type, broker)
            )
            tasks.append(task)
        
        # Wait for all connections
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self):
        """Stop all WebSocket connections"""
        self._running = False
        logger.info("Stopping WebSocket connections...")
        
        # Close all connections
        for broker_type in list(self.connections.keys()):
            await self._close_connection(broker_type)
        
        logger.info("All WebSocket connections stopped")
    
    async def _maintain_connection(self, broker_type: BrokerType, broker: BrokerAdapter):
        """
        Maintain WebSocket connection with auto-reconnect.
        
        Args:
            broker_type: Broker type
            broker: Broker adapter instance
        """
        reconnect_delay = 5  # seconds
        
        while self._running:
            try:
                logger.info(f"Connecting to {broker_type.value} WebSocket...")
                
                # Connect to broker WebSocket
                # Note: Actual implementation depends on broker SDK
                # This is a placeholder for the connection logic
                
                connection = await self._connect_broker_websocket(broker)
                self.connections[broker_type] = connection
                
                logger.info(f"Connected to {broker_type.value} WebSocket")
                
                # Subscribe to symbols
                await self._subscribe_broker_symbols(broker_type, connection)
                
                # Listen for ticks
                await self._listen_for_ticks(broker_type, connection)
                
            except Exception as e:
                logger.error(f"WebSocket error for {broker_type.value}: {e}")
                
                # Close connection
                await self._close_connection(broker_type)
                
                # Wait before reconnecting
                if self._running:
                    logger.info(f"Reconnecting to {broker_type.value} in {reconnect_delay}s...")
                    await asyncio.sleep(reconnect_delay)
    
    async def _connect_broker_websocket(self, broker: BrokerAdapter) -> Any:
        """
        Connect to broker WebSocket.
        
        Note: This is a placeholder. Actual implementation depends on broker SDK.
        Each broker has different WebSocket implementation.
        """
        # TODO: Implement broker-specific WebSocket connection
        # For now, return a placeholder
        return None
    
    async def _subscribe_broker_symbols(self, broker_type: BrokerType, connection: Any):
        """Subscribe to all symbols for this broker"""
        for key, brokers in self.subscriptions.items():
            if broker_type in brokers:
                exchange, symbol = key.split(":")
                # TODO: Implement broker-specific subscription
                logger.debug(f"Subscribed {symbol} on {broker_type.value}")
    
    async def _listen_for_ticks(self, broker_type: BrokerType, connection: Any):
        """
        Listen for tick updates from broker.
        
        Note: This is a placeholder. Actual implementation depends on broker SDK.
        """
        # TODO: Implement broker-specific tick listening
        # This would be an infinite loop that receives ticks
        pass
    
    async def _close_connection(self, broker_type: BrokerType):
        """Close WebSocket connection for broker"""
        if broker_type in self.connections:
            # TODO: Implement broker-specific connection close
            del self.connections[broker_type]
            logger.info(f"Closed WebSocket connection for {broker_type.value}")
    
    async def _process_tick(self, broker_type: BrokerType, tick_data: Dict[str, Any]):
        """
        Process tick data from broker.
        
        Args:
            broker_type: Source broker
            tick_data: Tick data from broker
        """
        # Cache in Redis
        symbol = tick_data.get("symbol")
        ltp = tick_data.get("ltp")
        
        if symbol and ltp:
            redis_key = f"tick:{broker_type.value}:{symbol}"
            await redis_client.setex(
                redis_key,
                5,  # 5 second TTL
                str({
                    "ltp": ltp,
                    "timestamp": datetime.now().isoformat(),
                    "broker": broker_type.value,
                    **tick_data
                })
            )
        
        # Broadcast to callbacks
        for callback in self.tick_callbacks:
            try:
                await callback({
                    "broker": broker_type.value,
                    **tick_data
                })
            except Exception as e:
                logger.error(f"Error in tick callback: {e}")
    
    def get_connection_status(self) -> Dict[BrokerType, bool]:
        """Get connection status for all brokers"""
        return {
            broker_type: broker_type in self.connections
            for broker_type in self.brokers.keys()
        }


# Global singleton instance
websocket_manager = WebSocketManager()
