"""
Risk Management API Endpoints
"""
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.risk_service import RiskService
from app.api.v1.endpoints.auth import get_current_user


router = APIRouter()


# Request/Response Models
class RiskLimitsUpdate(BaseModel):
    max_positions: Optional[int] = Field(None, ge=1, le=100)
    max_position_size: Optional[float] = Field(None, gt=0)
    max_portfolio_value: Optional[float] = Field(None, gt=0)
    max_daily_loss: Optional[float] = Field(None, gt=0)
    max_weekly_loss: Optional[float] = Field(None, gt=0)
    max_drawdown_pct: Optional[float] = Field(None, gt=0, le=100)
    max_sector_concentration_pct: Optional[float] = Field(None, gt=0, le=100)
    max_single_stock_pct: Optional[float] = Field(None, gt=0, le=100)


class KillSwitchRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)
    confirmed: bool = Field(..., description="Must be true to activate")


class KillSwitchDeactivateRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)


class AlertAcknowledgeRequest(BaseModel):
    alert_id: int


# Endpoints
@router.get("/dashboard")
async def get_risk_dashboard(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete risk dashboard with P&L, limits, and alerts
    
    Returns:
    - total_pnl: Overall profit/loss
    - daily_pnl: Today's P&L
    - weekly_pnl: Last 7 days P&L
    - position_count: Number of open positions
    - limits: Risk limits configuration
    - utilization: Limit utilization percentages
    - kill_switch: Kill switch status
    - alerts: Active alerts
    """
    risk_service = RiskService(db)
    dashboard = await risk_service.get_dashboard(current_user)
    return dashboard


@router.get("/limits")
async def get_risk_limits(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's risk limits"""
    risk_service = RiskService(db)
    limits = await risk_service.get_or_create_limits(current_user)
    
    return {
        'max_positions': limits.max_positions,
        'max_position_size': float(limits.max_position_size),
        'max_portfolio_value': float(limits.max_portfolio_value),
        'max_daily_loss': float(limits.max_daily_loss),
        'max_weekly_loss': float(limits.max_weekly_loss),
        'max_drawdown_pct': limits.max_drawdown_pct,
        'max_sector_concentration_pct': limits.max_sector_concentration_pct,
        'max_single_stock_pct': limits.max_single_stock_pct,
    }


@router.put("/limits")
async def update_risk_limits(
    limits_data: RiskLimitsUpdate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update risk limits"""
    risk_service = RiskService(db)
    
    # Convert to dict, excluding None values
    update_data = {k: v for k, v in limits_data.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    limits = await risk_service.update_limits(current_user, update_data)
    
    return {
        'success': True,
        'message': 'Risk limits updated successfully',
        'limits': {
            'max_positions': limits.max_positions,
            'max_position_size': float(limits.max_position_size),
            'max_daily_loss': float(limits.max_daily_loss),
            'max_weekly_loss': float(limits.max_weekly_loss),
        }
    }


@router.post("/kill-switch/activate")
async def activate_kill_switch(
    request: KillSwitchRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Activate kill switch - disables all trading
    
    Requires:
    - reason: Detailed reason (min 10 chars)
    - confirmed: Must be true
    """
    if not request.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kill switch activation must be confirmed"
        )
    
    risk_service = RiskService(db)
    
    # Check if already active
    limits = await risk_service.get_or_create_limits(current_user)
    if limits.kill_switch_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kill switch is already active"
        )
    
    result = await risk_service.activate_kill_switch(
        user_id=current_user,
        reason=request.reason,
        activated_by=current_user
    )
    
    return result


@router.post("/kill-switch/deactivate")
async def deactivate_kill_switch(
    request: KillSwitchDeactivateRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate kill switch - re-enables trading"""
    risk_service = RiskService(db)
    
    # Check if active
    limits = await risk_service.get_or_create_limits(current_user)
    if not limits.kill_switch_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kill switch is not active"
        )
    
    result = await risk_service.deactivate_kill_switch(
        user_id=current_user,
        reason=request.reason,
        deactivated_by=current_user
    )
    
    return result


@router.get("/positions/summary")
async def get_positions_summary(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of current positions for risk analysis"""
    risk_service = RiskService(db)
    metrics = await risk_service.calculate_current_metrics(current_user)
    
    return {
        'position_count': metrics['position_count'],
        'total_exposure': metrics['total_exposure'],
        'portfolio_value': metrics['portfolio_value'],
        'concentration_by_symbol': metrics['concentration_by_symbol'],
    }


@router.get("/check-limits")
async def check_risk_limits(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if any risk limits are breached"""
    risk_service = RiskService(db)
    breaches = await risk_service.check_limits(current_user)
    
    return {
        'breaches': breaches,
        'has_breaches': len(breaches) > 0,
        'critical_breaches': [b for b in breaches if b['severity'] == 'CRITICAL'],
    }


@router.post("/alerts/acknowledge")
async def acknowledge_alert(
    request: AlertAcknowledgeRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark an alert as acknowledged"""
    risk_service = RiskService(db)
    success = await risk_service.acknowledge_alert(request.alert_id, current_user)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return {'success': True, 'message': 'Alert acknowledged'}
