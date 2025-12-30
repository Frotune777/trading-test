"""
TA Configuration API Endpoints
Endpoints for managing TA Aggregator weights and viewing accuracy metrics.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.services.ta_aggregator import TAggregator
from app.database.models_quad import QUADUserPreferences

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ta", tags=["TA Configuration"])


@router.get("/weights")
async def get_all_regime_weights(
    db: AsyncSession = Depends(get_db)
):
    """
    Get weights for all market regimes.
    Returns custom weights if set, otherwise system defaults.
    """
    try:
        aggregator = TAggregator(db)
        regimes = ["TRENDING_UP", "TRENDING_DOWN", "RANGING", "VOLATILE", "UNKNOWN"]
        all_weights = {}
        
        for regime in regimes:
            all_weights[regime] = await aggregator._load_regime_weights(regime)
            
        return all_weights
    except Exception as e:
        logger.error(f"Error getting all regime weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/weights/{regime}")
async def update_regime_weights(
    regime: str,
    weights: Dict[str, float],
    db: AsyncSession = Depends(get_db)
):
    """
    Update weights for a specific market regime.
    - **regime**: TRENDING_UP, TRENDING_DOWN, RANGING, VOLATILE, UNKNOWN
    - **weights**: Dict of {trend, momentum, volatility, volume} summing to 1.0
    """
    aggregator = TAggregator(db)
    success = await aggregator.update_regime_weights(regime, weights)
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid weight configuration or database error")
        
    return {"status": "success", "message": f"Weights updated for {regime}", "weights": weights}


@router.get("/accuracy")
async def get_ta_accuracy(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical TA Aggregator signal accuracy.
    """
    aggregator = TAggregator(db)
    results = await aggregator.get_historical_accuracy(days)
    return results


@router.get("/performance")
async def get_indicator_performance(
    db: AsyncSession = Depends(get_db)
):
    """
    Get performance breakdown by indicator category.
    """
    aggregator = TAggregator(db)
    results = await aggregator.get_indicator_performance()
    return results
