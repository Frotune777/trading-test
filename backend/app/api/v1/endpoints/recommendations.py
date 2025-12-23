from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from ....services.recommendation_service import RecommendationService
from app.services.reasoning_service import ReasoningService
import logging

logger = logging.getLogger(__name__)

# Initialize reasoning service (singleton)
reasoning_service = ReasoningService()

router = APIRouter()

# Pydantic models for response
class TechnicalDetails(BaseModel):
    trend: str
    rsi: Optional[float] = None
    ma_alignment: Optional[bool] = None

class RecommendationResponse(BaseModel):
    symbol: str
    smart_score: float
    action: str
    technical_score: float
    fundamental_score: float
    strategy: str
    explanation: str
    technical_details: TechnicalDetails
    fundamental_details: dict
    derivatives_details: Optional[dict] = {}
    market_regime: Optional[dict] = {}
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None

@router.get("/", response_model=List[RecommendationResponse])
def get_recommendations(
    strategy: str = Query('balanced', enum=['growth', 'value', 'momentum', 'balanced']),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get stock recommendations based on selected strategy.
    
    Strategies:
    - **balanced**: Mix of technical and fundamental factors (Default)
    - **growth**: Focus on high revenue/profit growth
    - **value**: Focus on low PE, high ROE
    - **momentum**: Focus on technical trend and RSI
    """
    try:
        service = RecommendationService()
        recommendations = service.generate_recommendations(strategy=strategy, limit=limit)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/reasoning", response_model=dict)
async def get_reasoning(symbol: str):
    """
    Get QUAD reasoning analysis for a symbol.
    """
    if not symbol or len(symbol) < 2:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    
    try:
        logger.info(f"Fetching QUAD reasoning for {symbol}")
        result = reasoning_service.analyze_symbol(symbol.upper())
        
        if 'error' in result:
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {result['error']}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reasoning endpoint for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
