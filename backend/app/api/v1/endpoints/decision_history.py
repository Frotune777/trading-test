# app/api/v1/endpoints/decision_history.py

"""
QUAD v1.1 - Decision History API Endpoints

Provides REST API access to historical decision data, conviction timelines,
and pillar drift measurements.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta

from app.services.decision_history_service import get_decision_history_service, DecisionHistoryService
from app.core.conviction_timeline import ConvictionTimeline
from app.core.pillar_drift import PillarDriftMeasurement

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/decisions", tags=["decision-history"])


@router.get("/history/{symbol}")
async def get_decision_history(
    symbol: str,
    limit: Optional[int] = Query(None, description="Maximum number of decisions to return"),
    days: Optional[int] = Query(None, description="Number of days to look back"),
    service: DecisionHistoryService = Depends(get_decision_history_service)
):
    """
    Retrieve decision history for a symbol.
    
    Args:
        symbol: Symbol to retrieve history for (e.g., "RELIANCE")
        limit: Maximum number of decisions to return
        days: Number of days to look back (alternative to limit)
    
    Returns:
        DecisionHistory object with all historical decisions
    """
    try:
        start_date = None
        if days:
            start_date = datetime.now() - timedelta(days=days)
        
        history = service.get_history(
            symbol=symbol.upper(),
            limit=limit,
            start_date=start_date
        )
        
        return history.to_dict()
    
    except Exception as e:
        logger.error(f"Failed to retrieve history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve decision history: {str(e)}")


@router.get("/conviction-timeline/{symbol}")
async def get_conviction_timeline(
    symbol: str,
    days: int = Query(30, description="Number of days to analyze"),
    service: DecisionHistoryService = Depends(get_decision_history_service)
):
    """
    Build conviction timeline for a symbol.
    
    Analyzes how conviction has evolved over time, including:
    - Conviction volatility (signal stability)
    - Bias consistency (how often bias changes)
    - Conviction trend (increasing/decreasing/stable)
    - Recent bias streak
    
    Args:
        symbol: Symbol to analyze (e.g., "RELIANCE")
        days: Number of days to look back (default: 30)
    
    Returns:
        ConvictionTimeline with computed metrics
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        history = service.get_history(
            symbol=symbol.upper(),
            start_date=start_date
        )
        
        if not history.entries:
            raise HTTPException(
                status_code=404,
                detail=f"No decision history found for {symbol} in last {days} days"
            )
        
        # Build timeline from history
        timeline = ConvictionTimeline.from_decision_history(history)
        
        return timeline.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to build conviction timeline for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to build conviction timeline: {str(e)}")


@router.get("/pillar-drift/{symbol}")
async def get_pillar_drift(
    symbol: str,
    compare_latest: bool = Query(True, description="Compare latest two decisions"),
    from_timestamp: Optional[str] = Query(None, description="ISO timestamp of earlier decision"),
    to_timestamp: Optional[str] = Query(None, description="ISO timestamp of later decision"),
    service: DecisionHistoryService = Depends(get_decision_history_service)
):
    """
    Measure pillar drift between two analyses.
    
    Quantifies how pillar scores changed, including:
    - Score deltas for each pillar
    - Bias changes (e.g., NEUTRAL → BULLISH)
    - Top movers (pillars with largest changes)
    - Drift classification (STABLE/MODERATE/HIGH)
    
    Args:
        symbol: Symbol to analyze (e.g., "RELIANCE")
        compare_latest: If True, compare latest two decisions (default)
        from_timestamp: ISO timestamp of earlier decision (for custom comparison)
        to_timestamp: ISO timestamp of later decision (for custom comparison)
    
    Returns:
        PillarDriftMeasurement with drift metrics and explanation
    """
    try:
        symbol = symbol.upper()
        
        if compare_latest:
            # Get latest two decisions
            recent = service.get_recent_decisions(symbol, limit=2)
            
            if len(recent) < 2:
                raise HTTPException(
                    status_code=404,
                    detail=f"Need at least 2 decisions to measure drift. Found {len(recent)} for {symbol}"
                )
            
            # recent[0] is newest, recent[1] is previous
            current_entry = recent[0]
            previous_entry = recent[1]
        
        else:
            # Custom comparison by timestamp
            if not from_timestamp or not to_timestamp:
                raise HTTPException(
                    status_code=400,
                    detail="Must provide both from_timestamp and to_timestamp for custom comparison"
                )
            
            from_dt = datetime.fromisoformat(from_timestamp)
            to_dt = datetime.fromisoformat(to_timestamp)
            
            history = service.get_history(symbol, start_date=from_dt, end_date=to_dt)
            
            if len(history.entries) < 2:
                raise HTTPException(
                    status_code=404,
                    detail=f"Need at least 2 decisions in specified range. Found {len(history.entries)}"
                )
            
            # Find entries closest to specified timestamps
            previous_entry = min(history.entries, key=lambda e: abs((e.analysis_timestamp - from_dt).total_seconds()))
            current_entry = min(history.entries, key=lambda e: abs((e.analysis_timestamp - to_dt).total_seconds()))
        
        # Reconstruct TradeIntent-like objects for drift calculation
        # (We only need pillar scores and biases, which are stored in history)
        from app.core.pillar_drift import PillarScoreSnapshot
        from app.core.trade_intent import DirectionalBias
        
        prev_snapshot = PillarScoreSnapshot(
            timestamp=previous_entry.analysis_timestamp,
            scores=previous_entry.pillar_scores or {},
            biases=previous_entry.pillar_biases or {},
            calibration_version=previous_entry.calibration_version
        )
        
        curr_snapshot = PillarScoreSnapshot(
            timestamp=current_entry.analysis_timestamp,
            scores=current_entry.pillar_scores or {},
            biases=current_entry.pillar_biases or {},
            calibration_version=current_entry.calibration_version
        )
        
        # Calculate drift
        drift = PillarDriftMeasurement(
            symbol=symbol,
            previous_snapshot=prev_snapshot,
            current_snapshot=curr_snapshot
        )
        
        return drift.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate pillar drift for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate pillar drift: {str(e)}")


@router.get("/statistics/{symbol}")
async def get_decision_statistics(
    symbol: str,
    days: int = Query(30, description="Number of days to analyze"),
    service: DecisionHistoryService = Depends(get_decision_history_service)
):
    """
    Get statistical summary of decision history.
    
    Provides aggregate metrics including:
    - Total number of decisions
    - Average conviction score
    - Bias distribution (count of each bias type)
    - Conviction range (min/max)
    
    Args:
        symbol: Symbol to analyze (e.g., "RELIANCE")
        days: Number of days to look back (default: 30)
    
    Returns:
        Dictionary with statistical summary
    """
    try:
        stats = service.get_statistics(symbol.upper(), days=days)
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get statistics for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/latest/{symbol}")
async def get_latest_decision(
    symbol: str,
    service: DecisionHistoryService = Depends(get_decision_history_service)
):
    """
    Get the most recent decision for a symbol.
    
    Args:
        symbol: Symbol to retrieve decision for (e.g., "RELIANCE")
    
    Returns:
        DecisionHistoryEntry or 404 if no history exists
    """
    try:
        latest = service.get_latest_decision(symbol.upper())
        
        if not latest:
            raise HTTPException(
                status_code=404,
                detail=f"No decision history found for {symbol}"
            )
        
        return latest.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest decision for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get latest decision: {str(e)}")
