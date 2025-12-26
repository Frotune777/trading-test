"""
Sandbox Mode Service
Paper trading simulation without real broker calls.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import random

from app.brokers.base_adapter import Order, Position

logger = logging.getLogger(__name__)


class SandboxService:
    """
    Sandbox Mode - Paper Trading
    
    Features:
        - Simulated order execution
        - Virtual portfolio
        - Realistic fills
        - No real broker calls
    
    Compliance:
        - Rule #1-3: Safe testing without real execution
    """
    
    def __init__(self):
        self.virtual_portfolio: Dict[str, Position] = {}
        self.virtual_orders: Dict[str, Dict[str, Any]] = {}
        self.order_counter = 1000
        self.enabled = False
        
        logger.info("SandboxService initialized")
    
    def enable(self):
        """Enable sandbox mode"""
        self.enabled = True
        logger.warning("⚠️ SANDBOX MODE ENABLED - No real orders will be placed")
    
    def disable(self):
        """Disable sandbox mode"""
        self.enabled = False
        logger.info("Sandbox mode disabled")
    
    async def place_sandbox_order(self, order: Order) -> Dict[str, Any]:
        """
        Place simulated order.
        
        Args:
            order: Order object
            
        Returns:
            Simulated order response
        """
        if not self.enabled:
            logger.error("Sandbox mode not enabled")
            return None
        
        # Generate order ID
        order_id = f"SANDBOX_{self.order_counter}"
        self.order_counter += 1
        
        # Simulate order placement
        simulated_order = {
            "order_id": order_id,
            "symbol": order.symbol,
            "action": order.action,
            "quantity": order.quantity,
            "order_type": order.order_type,
            "price": order.price,
            "status": "PLACED",
            "placed_at": datetime.now(),
            "broker": "SANDBOX"
        }
        
        self.virtual_orders[order_id] = simulated_order
        
        # Simulate immediate fill for market orders
        if order.order_type == "MARKET":
            await self._simulate_fill(order_id, order)
        
        logger.info(
            f"📝 SANDBOX ORDER: {order.symbol} {order.action} {order.quantity} - "
            f"Order ID: {order_id}"
        )
        
        return {
            "order_id": order_id,
            "status": "PLACED",
            "broker": "sandbox",
            "message": "Simulated order (sandbox mode)"
        }
    
    async def _simulate_fill(self, order_id: str, order: Order):
        """Simulate order fill"""
        simulated_order = self.virtual_orders[order_id]
        
        # Simulate realistic price with small slippage
        base_price = order.price if order.price else 100.0
        slippage = random.uniform(-0.1, 0.1)  # ±0.1% slippage
        fill_price = base_price * (1 + slippage / 100)
        
        # Update order
        simulated_order["status"] = "COMPLETE"
        simulated_order["filled_quantity"] = order.quantity
        simulated_order["average_price"] = fill_price
        simulated_order["filled_at"] = datetime.now()
        
        # Update virtual portfolio
        await self._update_virtual_portfolio(order, fill_price)
        
        logger.info(
            f"✅ SANDBOX FILL: {order.symbol} {order.quantity} @ {fill_price:.2f} "
            f"(slippage: {slippage:.2f}%)"
        )
    
    async def _update_virtual_portfolio(self, order: Order, fill_price: float):
        """Update virtual portfolio after fill"""
        key = f"{order.symbol}:{order.exchange}"
        
        if key not in self.virtual_portfolio:
            self.virtual_portfolio[key] = Position(
                symbol=order.symbol,
                exchange=order.exchange,
                quantity=0,
                average_price=0.0,
                pnl=0.0,
                product=order.product_type
            )
        
        position = self.virtual_portfolio[key]
        
        if order.action == "BUY":
            # Add to position
            total_cost = (position.quantity * position.average_price) + (order.quantity * fill_price)
            position.quantity += order.quantity
            position.average_price = total_cost / position.quantity if position.quantity > 0 else 0
        else:  # SELL
            # Reduce position
            position.quantity -= order.quantity
            if position.quantity == 0:
                position.average_price = 0.0
    
    def get_sandbox_portfolio(self) -> List[Position]:
        """Get virtual portfolio"""
        return list(self.virtual_portfolio.values())
    
    def get_sandbox_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get simulated order status"""
        return self.virtual_orders.get(order_id)
    
    def reset_sandbox(self):
        """Reset sandbox portfolio and orders"""
        self.virtual_portfolio.clear()
        self.virtual_orders.clear()
        self.order_counter = 1000
        logger.info("Sandbox reset - portfolio and orders cleared")


# Global singleton instance
sandbox_service = SandboxService()
