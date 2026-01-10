"""
Execution Gate Service
CRITICAL COMPONENT: Enforces Rule 2 (Human Approval) and Rule 13/14 (Decision Validity).

This service acts as the mandatory checkpoint for all automated trading signals.
No trade can be executed without passing through this gate.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.database.models_decision import DecisionLedger
from app.database.models_action_center import PendingOrder, OrderApprovalLog
from app.brokers.base_adapter import Order

logger = logging.getLogger(__name__)

class ExecutionGate:
    """
    The Guardian of Execution.
    
    Responsibilities:
    1. Intercept ALL trade decisions.
    2. Block immediate execution.
    3. Persist decision as a PendingOrder.
    4. Validate decision freshness (Rule 14).
    5. Handle manual approval/rejection.
    6. Log every attempt (Rule 34).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def intercept_decision(self, decision: DecisionLedger) -> Optional[PendingOrder]:
        """
        Intercepts a TradeDecision and creates a PendingOrder.
        """
        try:
            # 0. Kill Switch Check (Rule 20)
            if not settings.EXECUTION_ENABLED:
                logger.warning(f"🛑 Execution Disabled. Intercepted decision {decision.decision_id} rejected automatically.")
                return None

            # 1. Validate inputs
            if not decision.decision_id:
                raise ValueError("Decision missing ID")
            
            if decision.final_decision == "HOLD":
                logger.info(f"Decision {decision.decision_id} is HOLD. No execution needed.")
                return None

            # 2. Extract order details (Rule 14 compliance)
            # Assuming decision.output_details contains the necessary order info
            order_data = decision.output_details or {}
            
            # 3. Create PendingOrder
            pending_order = PendingOrder(
                user_id=int(decision.user_id) if decision.user_id.isdigit() else 1, # Fallback or map user
                api_type="smartorder", # Default to smart order
                order_data=order_data,
                status="pending",
                created_at_ist=datetime.now(), # Use timezone aware in real impl
                strategy_name=decision.strategy_name_snapshot or "Unknown",
                decision_id=decision.decision_id
            )
            
            self.db.add(pending_order)
            await self.db.commit()
            await self.db.refresh(pending_order)
            
            logger.info(f"🛑 Execution Gate intercepted decision {decision.decision_id}. PendingOrder #{pending_order.id} created.")
            return pending_order

        except Exception as e:
            logger.error(f"Failed to intercept decision {decision.decision_id}: {str(e)}")
            await self.db.rollback()
            return None

    async def authorize_execution(self, pending_order_id: int, user_id: str) -> bool:
        """
        Manually authorizes a pending order for execution.
        
        Args:
            pending_order_id: ID of the pending order.
            user_id: ID of the user authorizing the trade.
            
        Returns:
            True if authorized and passed to broker, False otherwise.
        """
        try:
            # 1. Fetch Order
            stmt = select(PendingOrder).where(PendingOrder.id == pending_order_id)
            result = await self.db.execute(stmt)
            order = result.scalar_one_or_none()
            
            if not order:
                logger.error(f"PendingOrder {pending_order_id} not found.")
                return False
                
            # 0. Kill Switch Check (Rule 20) - Double check before sending to broker
            if not settings.EXECUTION_ENABLED:
                logger.error(f"🛑 Execution Disabled. Authorization for order {pending_order_id} blocked.")
                return False
                
            if order.status != "pending":
                logger.warning(f"PendingOrder {pending_order_id} is already {order.status}.")
                return False

            # 2. Check Validity Window (Rule 14)
            # Fetch associated decision to get validity window
            stmt_decision = select(DecisionLedger).where(DecisionLedger.decision_id == order.decision_id)
            result_decision = await self.db.execute(stmt_decision)
            decision = result_decision.scalar_one_or_none()
            
            if decision:
                validity_mins = decision.validity_window_mins
                deadline = order.created_at_ist.replace(tzinfo=None) + timedelta(minutes=validity_mins)
                
                if datetime.now() > deadline:
                    logger.warning(f"Order {pending_order_id} expired. Deadline: {deadline}, Now: {datetime.now()}")
                    await self.reject_execution(pending_order_id, "System", "Validity window expired")
                    return False
            
            # 3. Mark as Approved
            order.status = "approved"
            order.approved_at_ist = datetime.now()
            order.approved_by = user_id
            
            # 4. Log Approval (Rule 34)
            log = OrderApprovalLog(
                pending_order_id=order.id,
                action="approved",
                performed_by=user_id,
                reason="Manual Authorization"
            )
            self.db.add(log)
            
            await self.db.commit()
            logger.info(f"✅ Order {pending_order_id} AUTHORIZED by {user_id}. Proceeding to broker...")
            
            # NOTE: Actual broker submission happens in the calling layer (StrategyManager)
            # or we trigger it here if we inject BrokerGateway.
            # For strict separation, Gate just approves, Manager executes.
            return True

        except Exception as e:
            logger.error(f"Error authorizing order {pending_order_id}: {str(e)}")
            await self.db.rollback()
            return False

    async def reject_execution(self, pending_order_id: int, user_id: str, reason: str) -> bool:
        """
        Reject a pending order.
        """
        try:
            stmt = select(PendingOrder).where(PendingOrder.id == pending_order_id)
            result = await self.db.execute(stmt)
            order = result.scalar_one_or_none()
            
            if not order:
                return False
                
            order.status = "rejected"
            order.rejected_at_ist = datetime.now()
            order.rejected_by = user_id
            order.rejected_reason = reason
            
            log = OrderApprovalLog(
                pending_order_id=order.id,
                action="rejected",
                performed_by=user_id,
                reason=reason
            )
            self.db.add(log)
            
            await self.db.commit()
            logger.info(f"🚫 Order {pending_order_id} REJECTED by {user_id}. Reason: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error rejecting order {pending_order_id}: {str(e)}")
            await self.db.rollback()
            return False
