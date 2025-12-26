"""
QUAD Analytics API Endpoints
RESTful API for QUAD decision tracking, predictions, and alerts
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.database.models_quad import (
    QUADDecisionCreate, QUADDecisionResponse,
    ConvictionTimeline, PillarDriftAnalysis, CorrelationMatrix,
    QUADPredictionResponse, QUADAlertCreate, QUADAlertResponse,
    SignalAccuracyMetrics, PillarScores
)
from app.services.quad_analytics_service import QUADAnalyticsService
from app.services.quad_ml_service import QUADMLService
from app.services.quad_alert_service import QUADAlertService
from app.core.database import get_db

router = APIRouter(prefix="/quad", tags=["QUAD Analytics"])


# ==================== Decision Management ====================

@router.post("/decision", response_model=QUADDecisionResponse)
async def store_quad_decision(
    decision: QUADDecisionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Store a QUAD decision
    
    - **symbol**: Stock symbol
    - **conviction**: Conviction score (0-100)
    - **signal**: Trading signal (BUY/SELL/HOLD)
    - **pillars**: Pillar scores
    """
    service = QUADAnalyticsService(db)
    return await service.store_decision(decision)


@router.get("/{symbol}/history", response_model=List[QUADDecisionResponse])
async def get_decision_history(
    symbol: str,
    limit: int = Query(50, ge=1, le=200),
    signal_filter: Optional[str] = Query(None, regex="^(BUY|SELL|HOLD)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get QUAD decision history for a symbol
    
    - **symbol**: Stock symbol
    - **limit**: Maximum number of records (1-200)
    - **signal_filter**: Filter by signal type
    - **start_date**: Start date filter
    - **end_date**: End date filter
    """
    service = QUADAnalyticsService(db)
    return await service.get_decision_history(
        symbol=symbol,
        limit=limit,
        signal_filter=signal_filter,
        start_date=start_date,
        end_date=end_date
    )


# ==================== Timeline & Drift ====================

@router.get("/{symbol}/timeline", response_model=ConvictionTimeline)
async def get_conviction_timeline(
    symbol: str,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conviction timeline for a symbol
    
    - **symbol**: Stock symbol
    - **days**: Number of days to look back (7-365)
    """
    analytics_service = QUADAnalyticsService(db)
    ml_service = QUADMLService(db)
    
    # Get historical timeline
    timeline = await analytics_service.get_conviction_timeline(symbol, days)
    
    # Add ML predictions if available
    if timeline.historical:
        latest_decision = timeline.historical[-1]
        # Get latest pillar scores (would need to fetch from decision)
        # For now, predictions will be added separately
    
    return timeline


@router.post("/{symbol}/drift", response_model=Optional[PillarDriftAnalysis])
async def calculate_pillar_drift(
    symbol: str,
    current_pillars: PillarScores,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate pillar drift from previous analysis
    
    - **symbol**: Stock symbol
    - **current_pillars**: Current pillar scores
    """
    service = QUADAnalyticsService(db)
    return await service.calculate_pillar_drift(symbol, current_pillars)


# ==================== ML Predictions ====================

@router.post("/{symbol}/predict", response_model=Optional[QUADPredictionResponse])
async def predict_conviction(
    symbol: str,
    current_pillars: PillarScores,
    days_ahead: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db)
):
    """
    Predict future conviction score using ML
    
    - **symbol**: Stock symbol
    - **current_pillars**: Current pillar scores
    - **days_ahead**: Days to predict ahead (1-30)
    """
    service = QUADMLService(db)
    return await service.predict_conviction(symbol, current_pillars, days_ahead)


# ==================== Correlations ====================

@router.get("/{symbol}/correlations", response_model=Optional[CorrelationMatrix])
async def get_pillar_correlations(
    symbol: str,
    days: int = Query(90, ge=30, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get pillar correlation analysis
    
    - **symbol**: Stock symbol
    - **days**: Number of days to analyze (30-365)
    """
    service = QUADAnalyticsService(db)
    return await service.calculate_pillar_correlations(symbol, days)


# ==================== Signal Accuracy ====================

@router.get("/{symbol}/accuracy", response_model=SignalAccuracyMetrics)
async def get_signal_accuracy(
    symbol: str,
    days: int = Query(90, ge=30, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get signal accuracy metrics
    
    - **symbol**: Stock symbol
    - **days**: Number of days to analyze (30-365)
    """
    service = QUADAnalyticsService(db)
    return await service.get_signal_accuracy(symbol, days)


# ==================== Alerts ====================

@router.post("/alerts", response_model=QUADAlertResponse)
async def create_alert(
    alert: QUADAlertCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a QUAD alert
    
    - **symbol**: Stock symbol
    - **alert_type**: Type of alert
    - **threshold**: Threshold value
    - **channels**: Notification channels
    """
    service = QUADAlertService(db)
    user_id = None
    return await service.create_alert(alert, user_id)


@router.get("/alerts", response_model=List[QUADAlertResponse])
async def list_alerts(
    symbol: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    List QUAD alerts
    
    - **symbol**: Filter by symbol (optional)
    - **active_only**: Only return active alerts
    """
    service = QUADAlertService(db)
    user_id = None
    return await service.list_alerts(symbol, active_only, user_id)


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a QUAD alert"""
    service = QUADAlertService(db)
    success = await service.delete_alert(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert deleted successfully"}


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge a QUAD alert"""
    service = QUADAlertService(db)
    success = await service.acknowledge_alert(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert acknowledged"}
