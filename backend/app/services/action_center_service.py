"""
Action Center Service
Handles order approval workflow for semi-auto execution mode.
"""

import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import pytz

from app.database.models_action_center import PendingOrder, OrderApprovalLog
from app.database.models_user import User

logger = logging.getLogger(__name__)

# IST timezone for timestamps
IST = pytz.timezone('Asia/Kolkata')

class ActionCenterService:
    """Service for Action Center order approval workflow"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_pending_order(
        self,
        user_id: int,
        api_type: str,
        order_data: Dict[str, Any],
        strategy_name: Optional[str] = None,
        decision_id: Optional[str] = None
    ) -> PendingOrder:
        """
        Create a new pending order for approval.
        
        Args:
            user_id: User ID
            api_type: Order type (placeorder, smartorder, basketorder, splitorder)
            order_data: Complete order payload
            strategy_name: Optional strategy name
            decision_id: Optional decision ID for traceability
            
        Returns:
            PendingOrder: Created pending order
        """
        # Create pending order
        pending_order = PendingOrder(
            user_id=user_id,
            api_type=api_type,
            order_data=order_data,
            status='pending',
            strategy_name=strategy_name,
            decision_id=decision_id,
            created_at_ist=datetime.now(IST)
        )
        
        self.db.add(pending_order)
        self.db.commit()
        self.db.refresh(pending_order)
        
        logger.info(f"Created pending order {pending_order.id} for user {user_id} (type: {api_type})")
        return pending_order
    
    def get_pending_orders(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[PendingOrder]:
        """
        Get pending orders with optional filters.
        
        Args:
            user_id: Filter by user ID (None for all users)
            status: Filter by status (None for all statuses)
            limit: Maximum number of orders to return
            
        Returns:
            List[PendingOrder]: List of pending orders
        """
        query = select(PendingOrder)
        
        # Apply filters
        filters = []
        if user_id is not None:
            filters.append(PendingOrder.user_id == user_id)
        if status is not None:
            filters.append(PendingOrder.status == status)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Order by creation time (newest first)
        query = query.order_by(PendingOrder.created_at_ist.desc()).limit(limit)
        
        orders = self.db.execute(query).scalars().all()
        return list(orders)
    
    def get_order_by_id(self, order_id: int) -> Optional[PendingOrder]:
        """Get a specific pending order by ID"""
        return self.db.get(PendingOrder, order_id)
    
    def approve_order(
        self,
        order_id: int,
        approved_by: str,
        execute_immediately: bool = True
    ) -> Dict[str, Any]:
        """
        Approve a pending order.
        
        Args:
            order_id: Pending order ID
            approved_by: Username of approver
            execute_immediately: Whether to submit to broker immediately
            
        Returns:
            Dict with approval result and broker response
        """
        order = self.db.get(PendingOrder, order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        if order.status != 'pending':
            return {"success": False, "error": f"Order is already {order.status}"}
        
        # Update order status
        order.status = 'approved'
        order.approved_at_ist = datetime.now(IST)
        order.approved_by = approved_by
        
        # Log approval action
        log_entry = OrderApprovalLog(
            pending_order_id=order_id,
            action='approved',
            performed_by=approved_by,
            performed_at_ist=datetime.now(IST)
        )
        self.db.add(log_entry)
        
        # Submit to broker if requested
        broker_result = None
        if execute_immediately:
            broker_result = self._submit_to_broker(order)
            
            if broker_result.get('success'):
                order.status = 'executed'
                order.executed_at_ist = datetime.now(IST)
                order.broker_order_id = broker_result.get('order_id')
                order.broker_status = broker_result.get('status')
                order.broker_response = broker_result.get('response')
            else:
                order.status = 'failed'
                order.broker_response = broker_result
        
        self.db.commit()
        
        logger.info(f"Order {order_id} approved by {approved_by}")
        return {
            "success": True,
            "order_id": order_id,
            "status": order.status,
            "broker_result": broker_result
        }
    
    def reject_order(
        self,
        order_id: int,
        rejected_by: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reject a pending order.
        
        Args:
            order_id: Pending order ID
            rejected_by: Username of rejector
            reason: Optional rejection reason
            
        Returns:
            Dict with rejection result
        """
        order = self.db.get(PendingOrder, order_id)
        if not order:
            return {"success": False, "error": "Order not found"}
        
        if order.status != 'pending':
            return {"success": False, "error": f"Order is already {order.status}"}
        
        # Update order status
        order.status = 'rejected'
        order.rejected_at_ist = datetime.now(IST)
        order.rejected_by = rejected_by
        order.rejected_reason = reason
        
        # Log rejection action
        log_entry = OrderApprovalLog(
            pending_order_id=order_id,
            action='rejected',
            performed_by=rejected_by,
            performed_at_ist=datetime.now(IST),
            reason=reason
        )
        self.db.add(log_entry)
        self.db.commit()
        
        logger.info(f"Order {order_id} rejected by {rejected_by}: {reason}")
        return {
            "success": True,
            "order_id": order_id,
            "status": order.status
        }
    
    def bulk_approve(
        self,
        order_ids: List[int],
        approved_by: str
    ) -> Dict[str, Any]:
        """
        Approve multiple orders in bulk.
        
        Args:
            order_ids: List of pending order IDs
            approved_by: Username of approver
            
        Returns:
            Dict with bulk approval results
        """
        results = {
            "total": len(order_ids),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for order_id in order_ids:
            result = self.approve_order(order_id, approved_by, execute_immediately=True)
            
            if result.get('success'):
                results["successful"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append({
                "order_id": order_id,
                "success": result.get('success'),
                "error": result.get('error')
            })
        
        logger.info(f"Bulk approved {results['successful']}/{results['total']} orders by {approved_by}")
        return results
    
    def get_statistics(self, user_id: Optional[int] = None) -> Dict[str, int]:
        """
        Get approval statistics.
        
        Args:
            user_id: Filter by user ID (None for all users)
            
        Returns:
            Dict with statistics
        """
        query = select(PendingOrder)
        if user_id is not None:
            query = query.where(PendingOrder.user_id == user_id)
        
        all_orders = self.db.execute(query).scalars().all()
        
        stats = {
            "total": len(all_orders),
            "pending": sum(1 for o in all_orders if o.status == 'pending'),
            "approved": sum(1 for o in all_orders if o.status == 'approved'),
            "rejected": sum(1 for o in all_orders if o.status == 'rejected'),
            "executed": sum(1 for o in all_orders if o.status == 'executed'),
            "failed": sum(1 for o in all_orders if o.status == 'failed')
        }
        
        return stats
    
    def parse_order_details(self, order: PendingOrder) -> Dict[str, Any]:
        """
        Parse order data for display.
        
        Args:
            order: PendingOrder object
            
        Returns:
            Dict with parsed order details
        """
        order_data = order.order_data
        api_type = order.api_type
        
        # Common fields
        details = {
            "id": order.id,
            "api_type": api_type,
            "status": order.status,
            "created_at": order.created_at_ist.isoformat() if order.created_at_ist else None,
            "strategy": order.strategy_name or order_data.get('strategy', 'N/A')
        }
        
        # Parse based on API type
        if api_type == 'basketorder':
            orders = order_data.get('orders', [])
            details.update({
                "symbol": f"Basket ({len(orders)} orders)",
                "exchange": "Multiple" if len(orders) > 1 else orders[0].get('exchange', '') if orders else '',
                "action": "Multiple" if len(orders) > 1 else orders[0].get('action', '') if orders else '',
                "quantity": str(sum(int(o.get('quantity', 0)) for o in orders)),
                "price_type": "Multiple"
            })
        else:
            # placeorder, smartorder, splitorder
            details.update({
                "symbol": order_data.get('symbol', ''),
                "exchange": order_data.get('exchange', ''),
                "action": order_data.get('action', ''),
                "quantity": str(order_data.get('quantity', '')),
                "price": str(order_data.get('price', '0')),
                "price_type": order_data.get('pricetype', order_data.get('price_type', 'MARKET')),
                "product_type": order_data.get('product', order_data.get('product_type', ''))
            })
        
        return details
    
    def _submit_to_broker(self, order: PendingOrder) -> Dict[str, Any]:
        """
        Submit order to broker (placeholder for actual broker integration).
        
        Args:
            order: PendingOrder to submit
            
        Returns:
            Dict with broker response
        """
        # TODO: Integrate with actual broker service (OpenAlgo)
        # For now, return a mock success response
        logger.warning(f"MOCK: Submitting order {order.id} to broker (not implemented)")
        
        return {
            "success": True,
            "order_id": f"MOCK_{order.id}",
            "status": "PENDING",
            "response": {
                "message": "Mock broker submission - integration pending"
            }
        }
