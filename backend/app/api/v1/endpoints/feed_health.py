"""
Feed Health API Endpoints
Provides real-time feed health status and metrics.
Complies with Rule #40 (UI must show feed health clearly).
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging

from app.services.feed_health_monitor import feed_health_monitor
from app.services.data_pipeline_service import data_pipeline_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status", response_model=Dict[str, Any])
async def get_feed_health_status():
    """
    Get current feed health status.
    
    Returns:
        Current health status with component details
        
    Compliance:
        - Rule #11: If feed health not HEALTHY, assume UNSAFE
        - Rule #40: UI must show feed health clearly
    """
    try:
        health_data = await feed_health_monitor.check_health()
        return health_data
    except Exception as e:
        logger.error(f"Error getting feed health status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=Dict[str, Any])
async def get_feed_health_metrics():
    """
    Get detailed feed health metrics.
    
    Returns:
        Detailed metrics including active/stale symbols, component health
    """
    try:
        health_data = await feed_health_monitor.check_health()
        pipeline_health = await data_pipeline_service.get_feed_health()
        
        return {
            "overall_status": health_data["status"],
            "components": health_data["components"],
            "metrics": {
                **health_data["metrics"],
                "pipeline": {
                    "circuit_breaker_active": pipeline_health.get("circuit_breaker_active", False),
                    "consecutive_failures": pipeline_health.get("consecutive_failures", 0)
                }
            },
            "timestamp": health_data["timestamp"]
        }
    except Exception as e:
        logger.error(f"Error getting feed health metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_feed_health_history(limit: int = 20):
    """
    Get historical feed health data.
    
    Args:
        limit: Number of historical records to return (default: 20)
        
    Returns:
        List of historical health checks
    """
    try:
        history = await feed_health_monitor.get_health_history(limit=limit)
        return history
    except Exception as e:
        logger.error(f"Error getting feed health history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/circuit-breaker/reset")
async def reset_circuit_breaker():
    """
    Manually reset the data pipeline circuit breaker.
    
    Returns:
        Success message
        
    Note:
        Use with caution. Only reset if you've verified the underlying issue is resolved.
    """
    try:
        await data_pipeline_service.reset_circuit_breaker()
        return {
            "success": True,
            "message": "Circuit breaker reset successfully"
        }
    except Exception as e:
        logger.error(f"Error resetting circuit breaker: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/start")
async def start_feed_monitor():
    """
    Start the feed health monitoring background task.
    
    Returns:
        Success message
    """
    try:
        await feed_health_monitor.start_monitoring()
        return {
            "success": True,
            "message": "Feed health monitor started"
        }
    except Exception as e:
        logger.error(f"Error starting feed monitor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/stop")
async def stop_feed_monitor():
    """
    Stop the feed health monitoring background task.
    
    Returns:
        Success message
    """
    try:
        await feed_health_monitor.stop_monitoring()
        return {
            "success": True,
            "message": "Feed health monitor stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping feed monitor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
