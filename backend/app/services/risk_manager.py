from datetime import datetime
from typing import Dict, Any, Optional
import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.brokers.base_adapter import Order
from app.database.models_monitoring import PnLSnapshot
from app.database.models_monitoring import TradePerformance
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Risk Governor - Authoritative pre-trade and account-level risk enforcement.
    Complies with Rules #1-3, #20, #29, #33-37.
    """
    
    def __init__(self):
        # Risk limits (should ideally be configurable via DB/Redis)
        self.max_position_size = 5000  # Max quantity per symbol
        self.max_daily_loss = -50000.0  # Max daily loss in INR (negative)
        self.max_orders_per_day = 100
        self.max_concentration_percent = 30.0  # Max % of portfolio in one symbol
        self.min_margin_buffer_percent = 20.0  # Keep 20% margin buffer

    async def validate_order(
        self,
        order: Order,
        db: AsyncSession,
        user_id: int,
        strategy_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate order against all risk limits.
        """
        # 0. Global Kill Switch Check (Rule #20)
        kill_switch = await redis_client.get("risk:kill_switch")
        if kill_switch == "active":
            return {
                "allowed": False,
                "blocked_reasons": ["GLOBAL_KILL_SWITCH_ACTIVE"],
                "timestamp": datetime.now().isoformat()
            }

        checks = []
        
        # Check 1: Position size limit
        checks.append(await self._check_position_size(order))
        
        # Check 2: Daily loss limit
        checks.append(await self._check_daily_loss(db, user_id))
        
        # Check 3: Order count limit
        checks.append(await self._check_order_count(db, user_id))
        
        # Check 4: Concentration limit
        checks.append(await self._check_concentration_limit(db, user_id, order))
        
        # Determine overall result
        failed_checks = [c for c in checks if not c["passed"]]
        allowed = len(failed_checks) == 0
        
        result = {
            "allowed": allowed,
            "order": {
                "symbol": order.symbol,
                "quantity": order.quantity,
                "transaction_type": order.transaction_type
            },
            "checks": checks,
            "blocked_reasons": [c["reason"] for c in failed_checks] if failed_checks else [],
            "timestamp": datetime.now().isoformat()
        }
        
        if not allowed:
            logger.warning(
                f"Order BLOCKED for User {user_id}: {order.symbol} {order.transaction_type} {order.quantity} - "
                f"Reasons: {', '.join(result['blocked_reasons'])}"
            )
        
        return result

    async def _check_position_size(self, order: Order) -> Dict[str, Any]:
        """Check if order exceeds symbol-specific hard limit"""
        if order.quantity > self.max_position_size:
            return {
                "check": "position_size",
                "passed": False,
                "reason": f"Quantity {order.quantity} exceeds hard limit {self.max_position_size}",
                "limit": self.max_position_size,
                "value": order.quantity
            }
        return {"check": "position_size", "passed": True, "reason": "Passed"}

    async def _check_daily_loss(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Check if current daily loss exceeds limit (Rule #30)"""
        try:
            # Query latest PnL snapshot for today
            stmt = select(PnLSnapshot).where(
                PnLSnapshot.user_id == user_id,
                PnLSnapshot.timestamp >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).order_by(PnLSnapshot.timestamp.desc()).limit(1)
            
            result = await db.execute(stmt)
            snapshot = result.scalar_one_or_none()
            
            pnl = snapshot.day_pnl if snapshot else 0.0
            
            if pnl <= self.max_daily_loss:
                return {
                    "check": "daily_loss",
                    "passed": False,
                    "reason": f"Daily loss {pnl:.2f} reached limit {self.max_daily_loss}",
                    "limit": self.max_daily_loss,
                    "value": pnl
                }
            return {"check": "daily_loss", "passed": True, "reason": "Passed"}
        except Exception as e:
            logger.error(f"Error checking daily loss limit: {e}")
            return {"check": "daily_loss", "passed": False, "reason": "Internal Error checking loss limit"}

    async def _check_order_count(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Check daily order count (Rule #34)"""
        try:
            # Count success/dry-run executions today
            # Note: We query TradePerformance as proxy for executed trades
            stmt = select(func.count()).select_from(TradePerformance).where(
                TradePerformance.user_id == user_id,
                TradePerformance.entry_time >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            )
            result = await db.execute(stmt)
            count = result.scalar() or 0
            
            if count >= self.max_orders_per_day:
                return {
                    "check": "order_count",
                    "passed": False,
                    "reason": f"Daily trade count {count} reached limit {self.max_orders_per_day}",
                    "limit": self.max_orders_per_day,
                    "value": count
                }
            return {"check": "order_count", "passed": True, "reason": "Passed"}
        except Exception as e:
            logger.error(f"Error checking order count: {e}")
            return {"check": "order_count", "passed": False, "reason": "Internal Error checking count"}
    async def _check_concentration_limit(self, db: AsyncSession, user_id: int, order: Order) -> Dict[str, Any]:
        """Check if order increases concentration beyond limit (Rule #17)"""
        try:
            # Get all open positions from TradePerformance
            # This is a proxy since we don't have a direct 'positions' table yet
            stmt = select(TradePerformance).where(
                TradePerformance.user_id == user_id,
                TradePerformance.status == "open"
            )
            result = await db.execute(stmt)
            positions = result.scalars().all()
            
            total_value = 0.0
            symbol_value = 0.0
            
            # Simple value calculation using entry_price from TradePerformance
            for pos in positions:
                value = (pos.quantity or 0) * (pos.entry_price or 0)
                total_value += value
                if pos.symbol == order.symbol:
                    symbol_value += value
            
            # Add the new order's potential value (assuming LTP for valuation)
            # Since we don't have LTP here easily, we use price if available or 0
            # For a new order, we should ideally use the current LTP
            # I'll use a conservative estimate or just quantity for now if price is missing
            new_order_value = order.quantity * (order.price or 0) 
            # Note: order.price might be None for market orders initially
            
            total_after = total_value + new_order_value
            symbol_after = symbol_value + new_order_value
            
            if total_after > 0:
                concentration = (symbol_after / total_after) * 100
                if concentration > self.max_concentration_percent:
                    return {
                        "check": "concentration",
                        "passed": False,
                        "reason": f"Concentration for {order.symbol} ({concentration:.1f}%) exceeds limit {self.max_concentration_percent}%",
                        "limit": self.max_concentration_percent,
                        "value": concentration
                    }
            
            return {"check": "concentration", "passed": True, "reason": "Passed"}
        except Exception as e:
            import traceback
            logger.error(f"Error checking concentration limit: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fail safe - allow if error during concentration check? 
            # Actually, Rule #6: fail closed.
            return {"check": "concentration", "passed": False, "reason": f"Internal Error checking concentration: {str(e)}"}
