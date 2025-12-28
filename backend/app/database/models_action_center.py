"""
Action Center Database Models
Models for pending order queue and approval workflow.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base

class PendingOrder(Base):
    """
    Pending order queue for semi-auto execution mode.
    
    Workflow:
    1. Order created with status='pending'
    2. User approves → status='approved', submitted to broker
    3. User rejects → status='rejected', not submitted
    4. Broker confirms → status='executed'
    """
    __tablename__ = "pending_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Order details
    api_type = Column(String(50), nullable=False)  # placeorder, smartorder, basketorder, splitorder
    order_data = Column(JSON, nullable=False)  # Complete order payload
    
    # Status tracking
    status = Column(String(20), default='pending', nullable=False, index=True)
    # Status values: pending, approved, rejected, executed, failed
    
    # Timestamps (IST for audit compliance)
    created_at_ist = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    approved_at_ist = Column(DateTime(timezone=True), nullable=True)
    rejected_at_ist = Column(DateTime(timezone=True), nullable=True)
    executed_at_ist = Column(DateTime(timezone=True), nullable=True)
    
    # Approval/Rejection tracking
    approved_by = Column(String(255), nullable=True)  # Username who approved
    rejected_by = Column(String(255), nullable=True)  # Username who rejected
    rejected_reason = Column(Text, nullable=True)
    
    # Broker execution
    broker_order_id = Column(String(255), nullable=True)
    broker_status = Column(String(50), nullable=True)
    broker_response = Column(JSON, nullable=True)
    
    # Strategy context
    strategy_name = Column(String(100), nullable=True)
    decision_id = Column(String(100), nullable=True)  # Link to TradeDecision
    
    # Performance indexes
    __table_args__ = (
        Index('idx_pending_orders_user_status', 'user_id', 'status'),
        Index('idx_pending_orders_created_at', 'created_at_ist'),
        Index('idx_pending_orders_status_created', 'status', 'created_at_ist'),
    )
    
    def __repr__(self):
        return f"<PendingOrder(id={self.id}, user_id={self.user_id}, status='{self.status}', api_type='{self.api_type}')>"


class OrderApprovalLog(Base):
    """
    Audit log for all approval/rejection actions.
    Provides immutable record of who did what and when.
    """
    __tablename__ = "order_approval_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    pending_order_id = Column(Integer, ForeignKey('pending_orders.id'), nullable=False, index=True)
    
    # Action details
    action = Column(String(20), nullable=False)  # approved, rejected, executed
    performed_by = Column(String(255), nullable=False)  # Username
    performed_at_ist = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Additional context
    reason = Column(Text, nullable=True)
    action_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    
    # Performance indexes
    __table_args__ = (
        Index('idx_approval_logs_order_id', 'pending_order_id'),
        Index('idx_approval_logs_performed_at', 'performed_at_ist'),
    )
    
    def __repr__(self):
        return f"<OrderApprovalLog(id={self.id}, order_id={self.pending_order_id}, action='{self.action}')>"
