# app/api/v1/endpoints/analytics.py

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from app.services.analytics_service import PostTradeAnalytics

router = APIRouter()
analytics = PostTradeAnalytics()

@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_metrics(days: int = Query(30, ge=1)):
    """
    Get aggregated performance metrics for the last N days.
    """
    try:
        return analytics.calculate_performance_metrics(days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/replay", response_model=List[Dict[str, Any]])
async def get_trade_replay(symbol: Optional[str] = None):
    """
    Get chronological trade log with running P&L.
    """
    try:
        return analytics.generate_trade_replay(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
