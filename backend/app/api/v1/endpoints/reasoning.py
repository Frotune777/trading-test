"""
Reasoning Engine API Endpoint
Provides QUAD analytics data for frontend consumption
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.services.reasoning_service import ReasoningService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize reasoning service (singleton)
reasoning_service = ReasoningService()


@router.get("/{symbol}/reasoning", response_model=Dict[str, Any])
async def get_reasoning(symbol: str) -> Dict[str, Any]:
    """
    Get QUAD reasoning analysis for a symbol.
    
    Returns TradeIntent v1.0 contract with:
    - directional_bias (BULLISH/BEARISH/NEUTRAL/INVALID)
    - conviction_score (0-100)
    - pillar_scores (6 pillars with scores and biases)
    - quality metadata (active/placeholder pillars)
    - execution_ready flag
    - degradation_warnings
    
    Args:
        symbol: Stock symbol (e.g., RELIANCE, TCS)
        
    Returns:
        Dict containing full reasoning analysis
        
    Raises:
        HTTPException: If symbol is invalid or analysis fails
    """
    if not symbol or len(symbol) < 2:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    
    try:
        logger.info(f"Fetching QUAD reasoning for {symbol}")
        result = reasoning_service.analyze_symbol(symbol.upper())
        
        # Check if analysis failed
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
