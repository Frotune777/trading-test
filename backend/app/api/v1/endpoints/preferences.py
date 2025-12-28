"""
User Preferences API Endpoints
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Dict, Any

from app.core.database import get_db
from app.database.models_quad import QUADUserPreferences, QUADUserPreferencesCreate

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/preferences/weights")
async def get_weights(
    db: AsyncSession = Depends(get_db)
):
    """Get current QUAD pillar weights"""
    try:
        stmt = select(QUADUserPreferences).where(QUADUserPreferences.user_id == 'default')
        result = await db.execute(stmt)
        pref = result.scalar_one_or_none()
        
        if pref and pref.weights:
            return pref.weights
        
        # Return defaults if no custom weights
        return {
            'trend': 0.30,
            'momentum': 0.20,
            'volatility': 0.10,
            'liquidity': 0.10,
            'sentiment': 0.10,
            'regime': 0.20
        }
        
    except Exception as e:
        logger.error(f"Error getting weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preferences/weights")
async def set_weights(
    preferences: QUADUserPreferencesCreate,
    db: AsyncSession = Depends(get_db)
):
    """Set custom QUAD pillar weights"""
    try:
        # Validate sum
        total = sum(preferences.weights.values())
        if abs(total - 1.0) > 0.01:
             raise HTTPException(status_code=400, detail=f"Weights must sum to 1.0 (got {total})")
             
        # Check if exists
        stmt = select(QUADUserPreferences).where(QUADUserPreferences.user_id == 'default')
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.weights = preferences.weights
            existing.updated_at = db.func.now()
        else:
            new_pref = QUADUserPreferences(
                user_id='default',
                weights=preferences.weights
            )
            db.add(new_pref)
            
        await db.commit()
        return {"status": "success", "weights": preferences.weights}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting weights: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preferences/reset")
async def reset_weights(
    db: AsyncSession = Depends(get_db)
):
    """Reset weights to default"""
    try:
        stmt = select(QUADUserPreferences).where(QUADUserPreferences.user_id == 'default')
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            await db.delete(existing)
            await db.commit()
            
        return {"status": "success", "message": "Weights reset to default"}
        
    except Exception as e:
        logger.error(f"Error resetting weights: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
