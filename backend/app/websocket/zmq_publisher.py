"""
ZeroMQ Publisher
High-performance message distribution using ZeroMQ pub/sub
"""

import asyncio
import logging
import zmq
import zmq.asyncio
import msgpack
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ZMQPublisher:
    """ZeroMQ publisher for market data distribution"""
    
    def __init__(self, port: int = 5555):
        self.port = port
        self.context = None
        self.socket = None
        self.running = False
    
    async def start(self):
        """Start the ZMQ publisher"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{self.port}")
        self.running = True
        
        logger.info(f"✅ ZMQ Publisher started on port {self.port}")
    
    async def stop(self):
        """Stop the ZMQ publisher"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        logger.info("ZMQ Publisher stopped")
    
    async def publish(self, topic: str, data: Dict[str, Any]):
        """
        Publish message to a topic
        
        Args:
            topic: Topic name (e.g., "NSE:RELIANCE:ltp")
            data: Message data
        """
        if not self.running:
            logger.warning("ZMQ Publisher not running")
            return
        
        try:
            # Add timestamp if not present
            if "timestamp" not in data:
                data["timestamp"] = datetime.utcnow().isoformat()
            
            # Serialize with MessagePack (faster than JSON)
            message = msgpack.packb(data)
            
            # Publish: topic + message
            await self.socket.send_multipart([
                topic.encode('utf-8'),
                message
            ])
            
            logger.debug(f"Published to {topic}: {data}")
            
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}")
    
    async def publish_ltp(self, symbol: str, ltp: float):
        """Publish LTP (Last Traded Price)"""
        topic = f"{symbol}:ltp"
        data = {
            "symbol": symbol,
            "ltp": ltp,
            "type": "ltp"
        }
        await self.publish(topic, data)
    
    async def publish_quote(self, symbol: str, quote: Dict[str, Any]):
        """Publish full quote data"""
        topic = f"{symbol}:quote"
        data = {
            "symbol": symbol,
            "type": "quote",
            **quote
        }
        await self.publish(topic, data)
    
    async def publish_full(self, symbol: str, full_data: Dict[str, Any]):
        """Publish full market depth"""
        topic = f"{symbol}:full"
        data = {
            "symbol": symbol,
            "type": "full",
            **full_data
        }
        await self.publish(topic, data)


class ZMQSubscriber:
    """ZeroMQ subscriber for consuming market data"""
    
    def __init__(self, host: str = "localhost", port: int = 5555):
        self.host = host
        self.port = port
        self.context = None
        self.socket = None
        self.running = False
        self.subscriptions = set()
    
    async def start(self):
        """Start the ZMQ subscriber"""
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"tcp://{self.host}:{self.port}")
        self.running = True
        
        logger.info(f"✅ ZMQ Subscriber connected to {self.host}:{self.port}")
    
    async def stop(self):
        """Stop the ZMQ subscriber"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        logger.info("ZMQ Subscriber stopped")
    
    async def subscribe(self, topic: str):
        """Subscribe to a topic"""
        if topic not in self.subscriptions:
            self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)
            self.subscriptions.add(topic)
            logger.info(f"Subscribed to topic: {topic}")
    
    async def unsubscribe(self, topic: str):
        """Unsubscribe from a topic"""
        if topic in self.subscriptions:
            self.socket.setsockopt_string(zmq.UNSUBSCRIBE, topic)
            self.subscriptions.remove(topic)
            logger.info(f"Unsubscribed from topic: {topic}")
    
    async def receive(self):
        """Receive a message"""
        if not self.running:
            return None
        
        try:
            # Receive: topic + message
            topic_bytes, message_bytes = await self.socket.recv_multipart()
            
            topic = topic_bytes.decode('utf-8')
            data = msgpack.unpackb(message_bytes, raw=False)
            
            return topic, data
            
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    async def listen(self, callback):
        """Listen for messages and call callback"""
        while self.running:
            result = await self.receive()
            if result:
                topic, data = result
                await callback(topic, data)
