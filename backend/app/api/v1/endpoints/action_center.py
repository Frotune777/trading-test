"""
Action Center API Endpoints
Handles order approval workflow for semi-auto execution mode.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.services.action_center_service import ActionCenterService
from app.services.user_auth_service import UserAuthService
from app.api.v1.endpoints.auth import get_current_user
from app.database.models_user import User

router = APIRouter(prefix="/action-center", tags=["action-center"])

# Pydantic models
class OrderApprovalRequest(BaseModel):
    reason: Optional[str] = None

class OrderRejectionRequest(BaseModel):
    reason: str

class BulkApprovalRequest(BaseModel):
    order_ids: List[int]

class PendingOrderResponse(BaseModel):
    id: int
    user_id: int
    api_type: str
    status: str
    created_at_ist: datetime
    approved_at_ist: Optional[datetime]
    rejected_at_ist: Optional[datetime]
    approved_by: Optional[str]
    rejected_by: Optional[str]
    rejected_reason: Optional[str]
    broker_order_id: Optional[str]
    broker_status: Optional[str]
    strategy_name: Optional[str]
    decision_id: Optional[str]
    order_details: Dict[str, Any]
    
    class Config:
        from_attributes = True

class StatisticsResponse(BaseModel):
    total: int
    pending: int
    approved: int
    rejected: int
    executed: int
    failed: int

@router.get("/orders", response_model=List[PendingOrderResponse])
async def get_pending_orders(
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, rejected, executed, failed)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of orders to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get pending orders for the current user.
    
    - **status**: Optional filter by status
    - **limit**: Maximum number of orders (default: 100, max: 500)
    
    Returns orders sorted by creation time (newest first).
    """
    action_center = ActionCenterService(db)
    
    # Get orders for current user
    orders = action_center.get_pending_orders(
        user_id=current_user.id,
        status=status,
        limit=limit
    )
    
    # Parse order details for each order
    response = []
    for order in orders:
        order_dict = {
            "id": order.id,
            "user_id": order.user_id,
            "api_type": order.api_type,
            "status": order.status,
            "created_at_ist": order.created_at_ist,
            "approved_at_ist": order.approved_at_ist,
            "rejected_at_ist": order.rejected_at_ist,
            "approved_by": order.approved_by,
            "rejected_by": order.rejected_by,
            "rejected_reason": order.rejected_reason,
            "broker_order_id": order.broker_order_id,
            "broker_status": order.broker_status,
            "strategy_name": order.strategy_name,
            "decision_id": order.decision_id,
            "order_details": action_center.parse_order_details(order)
        }
        response.append(PendingOrderResponse(**order_dict))
    
    return response

@router.get("/orders/{order_id}", response_model=PendingOrderResponse)
async def get_order_details(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific pending order.
    
    - **order_id**: Pending order ID
    """
    action_center = ActionCenterService(db)
    
    order = action_center.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    
    # Verify user owns this order
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this order"
        )
    
    order_dict = {
        "id": order.id,
        "user_id": order.user_id,
        "api_type": order.api_type,
        "status": order.status,
        "created_at_ist": order.created_at_ist,
        "approved_at_ist": order.approved_at_ist,
        "rejected_at_ist": order.rejected_at_ist,
        "approved_by": order.approved_by,
        "rejected_by": order.rejected_by,
        "rejected_reason": order.rejected_reason,
        "broker_order_id": order.broker_order_id,
        "broker_status": order.broker_status,
        "strategy_name": order.strategy_name,
        "decision_id": order.decision_id,
        "order_details": action_center.parse_order_details(order)
    }
    
    return PendingOrderResponse(**order_dict)

@router.post("/orders/{order_id}/approve")
async def approve_order(
    order_id: int,
    approval_request: OrderApprovalRequest = OrderApprovalRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a pending order and submit to broker.
    
    - **order_id**: Pending order ID
    - **reason**: Optional approval reason
    
    This will immediately submit the order to the broker.
    """
    action_center = ActionCenterService(db)
    
    # Verify order exists and belongs to user
    order = action_center.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to approve this order"
        )
    
    # Approve order
    result = action_center.approve_order(
        order_id=order_id,
        approved_by=current_user.username,
        execute_immediately=True
    )
    
    if not result.get('success'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('error', 'Failed to approve order')
        )
    
    return {
        "message": "Order approved and submitted to broker",
        "order_id": order_id,
        "status": result.get('status'),
        "broker_result": result.get('broker_result')
    }

@router.post("/orders/{order_id}/reject")
async def reject_order(
    order_id: int,
    rejection_request: OrderRejectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a pending order.
    
    - **order_id**: Pending order ID
    - **reason**: Rejection reason (required)
    
    Rejected orders will not be submitted to the broker.
    """
    action_center = ActionCenterService(db)
    
    # Verify order exists and belongs to user
    order = action_center.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to reject this order"
        )
    
    # Reject order
    result = action_center.reject_order(
        order_id=order_id,
        rejected_by=current_user.username,
        reason=rejection_request.reason
    )
    
    if not result.get('success'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('error', 'Failed to reject order')
        )
    
    return {
        "message": "Order rejected",
        "order_id": order_id,
        "status": result.get('status')
    }

@router.post("/bulk-approve")
async def bulk_approve_orders(
    bulk_request: BulkApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve multiple orders in bulk.
    
    - **order_ids**: List of pending order IDs to approve
    
    All orders will be submitted to the broker immediately.
    """
    action_center = ActionCenterService(db)
    
    # Verify all orders belong to user
    for order_id in bulk_request.order_ids:
        order = action_center.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )
        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to approve order {order_id}"
            )
    
    # Bulk approve
    result = action_center.bulk_approve(
        order_ids=bulk_request.order_ids,
        approved_by=current_user.username
    )
    
    return {
        "message": f"Bulk approval completed: {result['successful']}/{result['total']} successful",
        "total": result['total'],
        "successful": result['successful'],
        "failed": result['failed'],
        "details": result['details']
    }

@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get approval statistics for the current user.
    
    Returns counts for each status: pending, approved, rejected, executed, failed.
    """
    action_center = ActionCenterService(db)
    
    stats = action_center.get_statistics(user_id=current_user.id)
    
    return StatisticsResponse(**stats)
