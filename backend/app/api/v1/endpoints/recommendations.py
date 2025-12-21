from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from ....services.recommendation_service import RecommendationService

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
