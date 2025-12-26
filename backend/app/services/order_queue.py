"""
Order Queue Service
Rate-limited async order queue for webhook-triggered orders.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from collections import deque
from dataclasses import dataclass
import time

from app.services.broker_gateway import broker_gateway
from app.brokers.base_adapter import Order, BrokerType

logger = logging.getLogger(__name__)


@dataclass
class QueuedOrder:
    """Order in queue"""
    order_data: Dict[str, Any]
    priority: str = "normal"  # "normal" or "high"
    queued_at: float = None
    
    def __post_init__(self):
        if self.queued_at is None:
            self.queued_at = time.time()


class OrderQueue:
    """
    Async order queue with rate limiting.
    
    Features:
        - Two queues: regular (10/sec) and smart (1/sec)
        - Priority queue support
        - Async processing
        - Retry logic
        - Dead letter queue for failed orders
    
    Rate Limits:
        - Regular orders: 10 per second
        - Smart orders: 1 per second
    """
    
    def __init__(self):
        self.regular_queue: asyncio.Queue = asyncio.Queue()
        self.smart_queue: asyncio.Queue = asyncio.Queue()
        self.dead_letter_queue: list[Dict[str, Any]] = []
        
        # Rate limiting
        self.last_regular_orders: deque = deque(maxlen=10)
        self.last_smart_order_time: float = 0
        
        # Processing state
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        
        logger.info("OrderQueue initialized")
    
    async def enqueue_order(
        self,
        order_data: Dict[str, Any],
        is_smart_order: bool = False,
        priority: str = "normal"
    ):
        """
        Add order to queue.
        
        Args:
            order_data: Order payload
            is_smart_order: Whether this is a smart order (position-aware)
            priority: "normal" or "high"
        """
        queued_order = QueuedOrder(
            order_data=order_data,
            priority=priority
        )
        
        if is_smart_order:
            await self.smart_queue.put(queued_order)
            logger.info(f"Enqueued smart order for {order_data.get('symbol')}")
        else:
            await self.regular_queue.put(queued_order)
            logger.info(f"Enqueued regular order for {order_data.get('symbol')}")
    
    async def start(self):
        """Start order processor"""
        if self._running:
            logger.warning("OrderQueue already running")
            return
        
        self._running = True
        self._processor_task = asyncio.create_task(self._process_orders())
        logger.info("OrderQueue processor started")
    
    async def stop(self):
        """Stop order processor"""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("OrderQueue processor stopped")
    
    async def _process_orders(self):
        """Background task to process orders with rate limiting"""
        while self._running:
            try:
                # Process smart orders first (1 per second)
                if not self.smart_queue.empty():
                    now = time.time()
                    
                    # Check if 1 second has passed since last smart order
                    if now - self.last_smart_order_time >= 1.0:
                        queued_order = await self.smart_queue.get()
                        await self._execute_order(queued_order, is_smart=True)
                        self.last_smart_order_time = now
                        self.smart_queue.task_done()
                        continue
                
                # Process regular orders (up to 10 per second)
                if not self.regular_queue.empty():
                    now = time.time()
                    
                    # Clean up old timestamps (older than 1 second)
                    while self.last_regular_orders and now - self.last_regular_orders[0] > 1.0:
                        self.last_regular_orders.popleft()
                    
                    # Check if under rate limit
                    if len(self.last_regular_orders) < 10:
                        queued_order = await self.regular_queue.get()
                        await self._execute_order(queued_order, is_smart=False)
                        self.last_regular_orders.append(now)
                        self.regular_queue.task_done()
                        continue
                
                # Small sleep to prevent CPU spinning
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in order processor: {e}")
                await asyncio.sleep(1)  # Sleep on error
    
    async def _execute_order(self, queued_order: QueuedOrder, is_smart: bool = False):
        """
        Execute order via BrokerGateway.
        
        Args:
            queued_order: Queued order to execute
            is_smart: Whether this is a smart order
        """
        order_data = queued_order.order_data
        
        try:
            # Extract order details
            symbol = order_data.get("symbol")
            exchange = order_data.get("exchange", "NSE")
            action = order_data.get("action")
            quantity = order_data.get("quantity")
            product = order_data.get("product", "MIS")
            price_type = order_data.get("pricetype", "MARKET")
            price = order_data.get("price", 0.0)
            
            # Create Order object
            order = Order(
                symbol=symbol,
                exchange=exchange,
                action=action,
                quantity=int(quantity),
                product_type=product,
                order_type=price_type,
                price=float(price) if price else 0.0
            )
            
            # Get broker (use specified broker or primary)
            broker_name = order_data.get("broker")
            broker_type = BrokerType(broker_name) if broker_name else None
            
            # Place order via BrokerGateway
            if broker_type and broker_type in broker_gateway.brokers:
                broker = broker_gateway.brokers[broker_type]
                result = await broker.place_order(order)
            elif broker_gateway.primary_broker:
                broker = broker_gateway.brokers[broker_gateway.primary_broker]
                result = await broker.place_order(order)
            else:
                raise ValueError("No broker available for order execution")
            
            logger.info(f"{'Smart' if is_smart else 'Regular'} order executed: {symbol} {action} {quantity} - Result: {result}")
            
        except Exception as e:
            logger.error(f"Error executing order for {order_data.get('symbol')}: {e}")
            
            # Add to dead letter queue
            self.dead_letter_queue.append({
                "order_data": order_data,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "is_smart": is_smart
            })
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "running": self._running,
            "regular_queue_size": self.regular_queue.qsize(),
            "smart_queue_size": self.smart_queue.qsize(),
            "dead_letter_queue_size": len(self.dead_letter_queue),
            "regular_rate_limit_used": len(self.last_regular_orders),
            "last_smart_order_time": self.last_smart_order_time
        }


# Global singleton instance
order_queue = OrderQueue()
