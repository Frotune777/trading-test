"""
Mock Broker Adapter
Simulates a broker for testing and development.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import pandas as pd

from app.brokers.base_adapter import BrokerAdapter, Order, Position, BrokerHealth, BrokerType

logger = logging.getLogger(__name__)

class MockBrokerAdapter(BrokerAdapter):
    """
    In-memory mock broker.
    """
    def __init__(self):
        super().__init__(BrokerType.OPENALGO) # Use any dummy type
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.connected = False
        
    @property
    def broker_name(self) -> str:
        return "MOCK_BROKER"
        
    async def connect(self) -> bool:
        self.connected = True
        logger.info("Mock Broker Connected")
        return True
        
    async def disconnect(self) -> bool:
        self.connected = False
        logger.info("Mock Broker Disconnected")
        return True
        
    async def get_health_status(self) -> BrokerHealth:
        return BrokerHealth(
            broker_name=self.broker_name,
            status="HEALTHY" if self.connected else "UNKNOWN",
            is_connected=self.connected,
            latency_ms=10,
            last_heartbeat=datetime.now(),
            details={"mode": "MOCK"}
        )
        
    async def get_health(self) -> BrokerHealth:
        return await self.get_health_status()

    async def get_ltp(self, symbol: str, exchange: str = "NSE") -> Optional[float]:
        return 1000.0
        
    async def get_historical_data(
        self,
        symbol: str,
        interval: str,
        from_date: datetime,
        to_date: datetime,
        exchange: str = "NSE"
    ) -> Optional[pd.DataFrame]:
        return pd.DataFrame()

    async def place_order(self, order: Order) -> Optional[Dict[str, Any]]:
        """Simulate order placement."""
        order_id = f"mock-{uuid.uuid4().hex[:8]}"
        # If order object passed, use it, assuming it's mutable or we copy
        # Order is Pydantic, so standardized.
        
        self.orders[order_id] = order
        
        # Update mock position
        pos = self.positions.get(order.symbol)
        qty = order.quantity
        price = order.price or 1000.0 # Mock price if None
        
        if not pos:
            pos = Position(
                symbol=order.symbol, exchange=order.exchange, quantity=0, 
                average_price=0.0, ltp=price, pnl=0.0, product=order.product
            )
            
        if order.transaction_type == "BUY":
            total_val = (pos.quantity * pos.average_price) + (qty * price)
            new_qty = pos.quantity + qty
            pos.average_price = total_val / new_qty if new_qty > 0 else 0.0
            pos.quantity = new_qty
        else: # SELL
            pos.quantity -= qty
            
        self.positions[order.symbol] = pos
        
        logger.info(f"Mock Order Placed: {order_id} for {order.symbol}")
        return {"order_id": order_id, "status": "COMPLETE"}
        
    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        order = self.orders.get(order_id)
        if not order:
             return None
        return {"status": "COMPLETE", "order_id": order_id} # Mock always complete

    async def get_positions(self) -> Optional[List[Position]]:
        return list(self.positions.values())
        
    # Extra method not in abstract but useful
    async def get_order_book(self) -> List[Order]:
        return list(self.orders.values())
