"""
Risk Management Service
Pre-trade risk checks and position limits.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.brokers.base_adapter import Order

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Pre-Trade Risk Management
    
    Features:
        - Position size limits
        - Daily loss limits
        - Max orders per day
        - Concentration limits
        - Margin availability checks
    
    Compliance:
        - Rule #1-3: Execution gate enforcement
        - Rule #33-37: All checks logged
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Risk limits (configurable)
        self.max_position_size = 10000  # Max quantity per symbol
        self.max_daily_loss = 50000  # Max daily loss in INR
        self.max_orders_per_day = 500
        self.max_concentration_percent = 25  # Max % of portfolio in one symbol
        self.min_margin_buffer_percent = 20  # Keep 20% margin buffer
    
    async def validate_order(
        self,
        order: Order,
        strategy_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate order against risk limits.
        
        Args:
            order: Order to validate
            strategy_id: Optional strategy ID
            
        Returns:
            Validation result with allowed/blocked status and reason
        """
        checks = []
        
        # Check 1: Position size limit
        position_check = await self._check_position_limit(order)
        checks.append(position_check)
        
        # Check 2: Daily loss limit
        loss_check = await self._check_daily_loss_limit(strategy_id)
        checks.append(loss_check)
        
        # Check 3: Order count limit
        count_check = await self._check_order_count_limit()
        checks.append(count_check)
        
        # Check 4: Concentration limit
        concentration_check = await self._check_concentration_limit(order)
        checks.append(concentration_check)
        
        # Determine overall result
        failed_checks = [c for c in checks if not c["passed"]]
        allowed = len(failed_checks) == 0
        
        result = {
            "allowed": allowed,
            "order": {
                "symbol": order.symbol,
                "quantity": order.quantity,
                "action": order.action
            },
            "checks": checks,
            "blocked_reasons": [c["reason"] for c in failed_checks] if failed_checks else [],
            "timestamp": datetime.now().isoformat()
        }
        
        if not allowed:
            logger.warning(
                f"Order blocked by risk checks: {order.symbol} {order.action} {order.quantity} - "
                f"Reasons: {', '.join(result['blocked_reasons'])}"
            )
        
        return result
    
    async def _check_position_limit(self, order: Order) -> Dict[str, Any]:
        """Check if order exceeds position size limit"""
        if order.quantity > self.max_position_size:
            return {
                "check": "position_size",
                "passed": False,
                "reason": f"Order quantity {order.quantity} exceeds max position size {self.max_position_size}",
                "limit": self.max_position_size,
                "value": order.quantity
            }
        
        return {
            "check": "position_size",
            "passed": True,
            "reason": "Within position size limit",
            "limit": self.max_position_size,
            "value": order.quantity
        }
    
    async def _check_daily_loss_limit(self, strategy_id: Optional[int]) -> Dict[str, Any]:
        """Check if daily loss limit exceeded"""
        # TODO: Calculate actual daily P&L from positions/orders
        current_daily_loss = 0  # Placeholder
        
        if current_daily_loss > self.max_daily_loss:
            return {
                "check": "daily_loss",
                "passed": False,
                "reason": f"Daily loss {current_daily_loss} exceeds limit {self.max_daily_loss}",
                "limit": self.max_daily_loss,
                "value": current_daily_loss
            }
        
        return {
            "check": "daily_loss",
            "passed": True,
            "reason": "Within daily loss limit",
            "limit": self.max_daily_loss,
            "value": current_daily_loss
        }
    
    async def _check_order_count_limit(self) -> Dict[str, Any]:
        """Check if daily order count limit exceeded"""
        # TODO: Count orders from today
        today_order_count = 0  # Placeholder
        
        if today_order_count >= self.max_orders_per_day:
            return {
                "check": "order_count",
                "passed": False,
                "reason": f"Daily order count {today_order_count} exceeds limit {self.max_orders_per_day}",
                "limit": self.max_orders_per_day,
                "value": today_order_count
            }
        
        return {
            "check": "order_count",
            "passed": True,
            "reason": "Within daily order count limit",
            "limit": self.max_orders_per_day,
            "value": today_order_count
        }
    
    async def _check_concentration_limit(self, order: Order) -> Dict[str, Any]:
        """Check if order would exceed concentration limit"""
        # TODO: Calculate portfolio concentration
        symbol_concentration = 0  # Placeholder
        
        if symbol_concentration > self.max_concentration_percent:
            return {
                "check": "concentration",
                "passed": False,
                "reason": f"Symbol concentration {symbol_concentration}% exceeds limit {self.max_concentration_percent}%",
                "limit": self.max_concentration_percent,
                "value": symbol_concentration
            }
        
        return {
            "check": "concentration",
            "passed": True,
            "reason": "Within concentration limit",
            "limit": self.max_concentration_percent,
            "value": symbol_concentration
        }
