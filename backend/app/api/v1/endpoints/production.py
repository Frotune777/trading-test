"""
Production API Endpoints
Risk, Analytics, Sandbox, Monitoring, and Audit endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.services.risk_manager import RiskManager
from app.services.execution_analytics import ExecutionAnalyticsService
from app.services.sandbox_service import sandbox_service
from app.services.monitoring_service import monitoring_service, AlertLevel, AlertChannel
from app.services.audit_logger import AuditLogger, AuditEventType
from app.brokers.base_adapter import Order
from app.core.database import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/production", tags=["Production Features"])
logger = logging.getLogger(__name__)


# Risk Management Endpoints

@router.post("/risk/validate")
async def validate_order_risk(
    order: Order,
    strategy_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Validate order against risk limits.
    
    Returns validation result with allowed/blocked status.
    """
    risk_manager = RiskManager(db)
    result = await risk_manager.validate_order(order, strategy_id)
    
    return result


# Execution Analytics Endpoints

@router.get("/analytics/broker/{broker}")
async def get_broker_analytics(
    broker: str,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get broker performance analytics."""
    analytics = ExecutionAnalyticsService(db)
    performance = analytics.get_broker_performance(broker, hours)
    
    return performance


@router.get("/analytics/strategy/{strategy_id}")
async def get_strategy_analytics(
    strategy_id: int,
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get strategy performance analytics."""
    analytics = ExecutionAnalyticsService(db)
    performance = analytics.get_strategy_performance(strategy_id, days)
    
    return performance


# Sandbox Endpoints

@router.post("/sandbox/enable")
async def enable_sandbox(
    current_user: str = Depends(get_current_user)
):
    """Enable sandbox mode (paper trading)."""
    sandbox_service.enable()
    
    return {
        "status": "enabled",
        "message": "Sandbox mode enabled - all orders will be simulated"
    }


@router.post("/sandbox/disable")
async def disable_sandbox(
    current_user: str = Depends(get_current_user)
):
    """Disable sandbox mode."""
    sandbox_service.disable()
    
    return {
        "status": "disabled",
        "message": "Sandbox mode disabled - orders will be placed with real brokers"
    }


@router.get("/sandbox/portfolio")
async def get_sandbox_portfolio(
    current_user: str = Depends(get_current_user)
):
    """Get virtual portfolio (sandbox mode)."""
    portfolio = sandbox_service.get_sandbox_portfolio()
    
    return {
        "enabled": sandbox_service.enabled,
        "positions": portfolio
    }


@router.post("/sandbox/reset")
async def reset_sandbox(
    current_user: str = Depends(get_current_user)
):
    """Reset sandbox portfolio and orders."""
    sandbox_service.reset_sandbox()
    
    return {
        "status": "reset",
        "message": "Sandbox portfolio and orders cleared"
    }


# Monitoring Endpoints

@router.get("/monitoring/health")
async def get_system_health(
    current_user: str = Depends(get_current_user)
):
    """Get overall system health status."""
    health = await monitoring_service.check_system_health()
    
    return health


@router.get("/monitoring/metrics")
async def get_system_metrics(
    current_user: str = Depends(get_current_user)
):
    """Get current system metrics."""
    metrics = monitoring_service.get_metrics()
    
    return metrics


@router.post("/monitoring/alert")
async def send_test_alert(
    level: AlertLevel,
    title: str,
    message: str,
    current_user: str = Depends(get_current_user)
):
    """Send test alert."""
    await monitoring_service.send_alert(level, title, message)
    
    return {
        "status": "sent",
        "level": level.value,
        "title": title
    }


# Audit Log Endpoints

@router.get("/audit/logs")
async def query_audit_logs(
    event_type: Optional[str] = None,
    strategy_id: Optional[int] = None,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Query audit logs."""
    audit_logger = AuditLogger(db)
    
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = AuditEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {event_type}"
            )
    
    logs = audit_logger.query_logs(
        event_type=event_type_enum,
        user_id=current_user,
        strategy_id=strategy_id,
        hours=hours,
        limit=limit
    )
    
    return {
        "total": len(logs),
        "logs": [
            {
                "id": log.id,
                "event_type": log.event_type,
                "user_id": log.user_id,
                "strategy_id": log.strategy_id,
                "broker": log.broker,
                "symbol": log.symbol,
                "action": log.action,
                "details": log.details,
                "created_at": log.created_at
            }
            for log in logs
        ]
    }
