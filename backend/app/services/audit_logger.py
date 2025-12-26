"""
Comprehensive Audit Logging
Tracks all system operations for compliance and debugging.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Audit event types"""
    ORDER_PLACED = "ORDER_PLACED"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    ORDER_REJECTED = "ORDER_REJECTED"
    POSITION_OPENED = "POSITION_OPENED"
    POSITION_CLOSED = "POSITION_CLOSED"
    STRATEGY_CREATED = "STRATEGY_CREATED"
    STRATEGY_ACTIVATED = "STRATEGY_ACTIVATED"
    STRATEGY_DEACTIVATED = "STRATEGY_DEACTIVATED"
    WEBHOOK_RECEIVED = "WEBHOOK_RECEIVED"
    RISK_CHECK_FAILED = "RISK_CHECK_FAILED"
    RECONCILIATION_RUN = "RECONCILIATION_RUN"
    DISCREPANCY_DETECTED = "DISCREPANCY_DETECTED"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class AuditLog(Base):
    """Audit log record"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(String(50), index=True)
    strategy_id = Column(Integer, index=True)
    broker = Column(String(20))
    symbol = Column(String(50))
    action = Column(String(20))
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class AuditLogger:
    """
    Comprehensive Audit Logger
    
    Compliance:
        - Rule #33: Every decision must be traceable
        - Rule #34: Every execution attempt must be logged
        - Rule #35: Every block must include a reason
        - Rule #36: Agent assumptions must be explicitly stated
        - Rule #37: Silent failures are not allowed
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def log_order(
        self,
        event_type: AuditEventType,
        order_id: str,
        broker: str,
        symbol: str,
        action: str,
        quantity: int,
        price: Optional[float] = None,
        user_id: Optional[str] = None,
        strategy_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log order-related event"""
        audit_details = {
            "order_id": order_id,
            "quantity": quantity,
            "price": price,
            **(details or {})
        }
        
        await self._create_log(
            event_type=event_type,
            user_id=user_id,
            strategy_id=strategy_id,
            broker=broker,
            symbol=symbol,
            action=action,
            details=audit_details
        )
    
    async def log_strategy_event(
        self,
        event_type: AuditEventType,
        strategy_id: int,
        strategy_name: str,
        user_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log strategy-related event"""
        audit_details = {
            "strategy_name": strategy_name,
            **(details or {})
        }
        
        await self._create_log(
            event_type=event_type,
            user_id=user_id,
            strategy_id=strategy_id,
            details=audit_details
        )
    
    async def log_webhook(
        self,
        webhook_id: str,
        strategy_id: int,
        symbol: str,
        action: str,
        payload: Dict[str, Any],
        result: str
    ):
        """Log webhook event"""
        await self._create_log(
            event_type=AuditEventType.WEBHOOK_RECEIVED,
            strategy_id=strategy_id,
            symbol=symbol,
            action=action,
            details={
                "webhook_id": webhook_id,
                "payload": payload,
                "result": result
            }
        )
    
    async def log_risk_check(
        self,
        order_details: Dict[str, Any],
        blocked: bool,
        reasons: list[str],
        user_id: Optional[str] = None,
        strategy_id: Optional[int] = None
    ):
        """Log risk check result"""
        await self._create_log(
            event_type=AuditEventType.RISK_CHECK_FAILED if blocked else AuditEventType.ORDER_PLACED,
            user_id=user_id,
            strategy_id=strategy_id,
            symbol=order_details.get("symbol"),
            action=order_details.get("action"),
            details={
                "blocked": blocked,
                "reasons": reasons,
                "order_details": order_details
            }
        )
    
    async def log_reconciliation(
        self,
        run_id: int,
        brokers_checked: list[str],
        discrepancies_found: int,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log reconciliation run"""
        await self._create_log(
            event_type=AuditEventType.RECONCILIATION_RUN,
            details={
                "run_id": run_id,
                "brokers_checked": brokers_checked,
                "discrepancies_found": discrepancies_found,
                **(details or {})
            }
        )
    
    async def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log system error"""
        await self._create_log(
            event_type=AuditEventType.SYSTEM_ERROR,
            details={
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {}
            }
        )
    
    async def _create_log(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        strategy_id: Optional[int] = None,
        broker: Optional[str] = None,
        symbol: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Create audit log entry"""
        log_entry = AuditLog(
            event_type=event_type.value,
            user_id=user_id,
            strategy_id=strategy_id,
            broker=broker,
            symbol=symbol,
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(log_entry)
        self.db.commit()
        
        logger.info(
            f"AUDIT: {event_type.value} - "
            f"User: {user_id}, Strategy: {strategy_id}, "
            f"Symbol: {symbol}, Action: {action}"
        )
    
    def query_logs(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        strategy_id: Optional[int] = None,
        hours: int = 24,
        limit: int = 100
    ) -> list[AuditLog]:
        """Query audit logs"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        query = self.db.query(AuditLog).filter(AuditLog.created_at >= cutoff)
        
        if event_type:
            query = query.filter(AuditLog.event_type == event_type.value)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if strategy_id:
            query = query.filter(AuditLog.strategy_id == strategy_id)
        
        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
