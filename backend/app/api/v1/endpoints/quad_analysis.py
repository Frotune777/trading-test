"""
QUAD Analysis API Endpoints
Manual trigger endpoints for on-demand QUAD analysis

ARCHITECTURAL COMPLIANCE:
- These endpoints WRITE to quad_decisions table
- Separate from quad_analytics.py (which is READ-ONLY)
- Only way to trigger analysis besides scheduled jobs
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.services.quad_analysis_engine import QUADAnalysisEngine
from app.database.models_quad import QUADDecisionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quad/analysis", tags=["QUAD Analysis"])


# Request/Response Models
class BatchAnalysisRequest(BaseModel):
    """Request model for batch analysis"""
    symbols: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbols": ["RELIANCE", "TCS", "INFY", "HDFCBANK"]
            }
        }


class BatchAnalysisResponse(BaseModel):
    """Response model for batch analysis"""
    total_requested: int
    successful: int
    failed: int
    decisions: List[QUADDecisionResponse]
    errors: List[dict]


# Endpoints
@router.post("/{symbol}", response_model=dict)
async def trigger_quad_analysis(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger QUAD analysis for a single symbol
    
    This endpoint:
    1. Fetches market data
    2. Computes all 6 pillar scores
    3. Calculates conviction
    4. Generates signal (BUY/SELL/HOLD)
    5. Persists to quad_decisions table
    
    Args:
        symbol: Stock symbol to analyze (e.g., "RELIANCE")
        
    Returns:
        QUADDecisionResponse: The created decision record
        
    Raises:
        HTTPException: If analysis fails
    """
    logger.info(f"Manual QUAD analysis triggered for {symbol}")
    
    try:
        engine = QUADAnalysisEngine(db)
        decision = await engine.analyze_symbol(symbol)
        
        # Serialize to dict with pillar scores
        response = {
            "id": decision.id,
            "symbol": decision.symbol,
            "timestamp": decision.timestamp.isoformat(),
            "conviction": decision.conviction,
            "signal": decision.signal,
            "pillars": {
                "trend": decision.trend_score,
                "momentum": decision.momentum_score,
                "volatility": decision.volatility_score,
                "liquidity": decision.liquidity_score,
                "sentiment": decision.sentiment_score,
                "regime": decision.regime_score
            },
            "reasoning_summary": decision.reasoning_summary,
            "current_price": decision.current_price,
            "volume": decision.volume,
            "created_at": decision.created_at.isoformat()
        }
        
        logger.info(f"Manual analysis complete for {symbol}: conviction={decision.conviction}")
        return response
        
    except Exception as e:
        logger.error(f"Manual analysis failed for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/batch", response_model=BatchAnalysisResponse)
async def trigger_batch_analysis(
    request: BatchAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger batch QUAD analysis for multiple symbols
    
    This endpoint analyzes multiple symbols in sequence and returns
    results for all successful analyses.
    
    Args:
        request: BatchAnalysisRequest with list of symbols
        
    Returns:
        BatchAnalysisResponse: Summary of batch analysis results
    """
    symbols = request.symbols
    logger.info(f"Batch QUAD analysis triggered for {len(symbols)} symbols")
    
    engine = QUADAnalysisEngine(db)
    
    successful_decisions = []
    errors = []
    
    for symbol in symbols:
        try:
            decision = await engine.analyze_symbol(symbol)
            successful_decisions.append(decision)
        except Exception as e:
            logger.error(f"Batch analysis failed for {symbol}: {e}")
            errors.append({
                "symbol": symbol,
                "error": str(e)
            })
    
    response = BatchAnalysisResponse(
        total_requested=len(symbols),
        successful=len(successful_decisions),
        failed=len(errors),
        decisions=successful_decisions,
        errors=errors
    )
    
    logger.info(f"Batch analysis complete: {response.successful}/{response.total_requested} successful")
    return response


@router.get("/status")
async def get_analysis_status():
    """
    Get QUAD analysis engine status
    
    Returns basic health check and configuration info
    """
    return {
        "status": "operational",
        "engine": "QUADAnalysisEngine",
        "version": "1.0.0",
        "features": {
            "single_analysis": True,
            "batch_analysis": True,
            "scheduled_analysis": True
        }
    }
