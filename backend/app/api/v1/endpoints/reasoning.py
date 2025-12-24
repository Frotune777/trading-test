"""
Reasoning Engine API Endpoint
Provides QUAD analytics data for frontend consumption
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from app.services.reasoning_service import ReasoningService
from app.services.decision_history_service import get_decision_history_service, DecisionHistoryService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize reasoning service (singleton)
reasoning_service = ReasoningService()


@router.get("/{symbol}/reasoning", response_model=Dict[str, Any])
async def get_reasoning(
    symbol: str,
    save_history: bool = True,  # v1.1: Auto-save to history
    history_service: DecisionHistoryService = Depends(get_decision_history_service)
) -> Dict[str, Any]:
    """
    Get QUAD reasoning analysis for a symbol.
    
    Returns TradeIntent v1.1 contract with:
    - directional_bias (BULLISH/BEARISH/NEUTRAL/INVALID)
    - conviction_score (0-100)
    - pillar_scores (6 pillars with scores and biases)
    - quality metadata (active/placeholder pillars)
    - calibration_version (v1.1)
    - pillar_weights_snapshot (v1.1)
    - execution_ready flag
    - degradation_warnings
    
    v1.1: Automatically saves decision to history for observability.
    
    Args:
        symbol: Stock symbol (e.g., RELIANCE, TCS)
        save_history: If True, save decision to history (default: True)
        
    Returns:
        Dict containing full reasoning analysis
        
    Raises:
        HTTPException: If symbol is invalid or analysis fails
    """
    if not symbol or len(symbol) < 2:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    
    try:
        logger.info(f"Fetching QUAD reasoning for {symbol}")
        result = await reasoning_service.analyze_symbol(symbol.upper())
        
        # Check if analysis failed
        if 'error' in result:
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {result['error']}"
            )
        
        # v1.1: Save decision to history (if enabled)
        if save_history and 'trade_intent' in result:
            try:
                trade_intent = result['trade_intent']
                decision_id = history_service.save_decision(trade_intent)
                logger.info(f"✅ Saved decision {decision_id} to history")
                
                # Add decision_id to response (optional metadata)
                result['decision_id'] = decision_id
            except Exception as e:
                # Log error but don't fail the request
                logger.error(f"Failed to save decision to history: {e}")
                result['history_save_error'] = str(e)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reasoning endpoint for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
