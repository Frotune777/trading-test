from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0-QUAD"
    }

@router.get("/health/openalgo", tags=["health"])
async def openalgo_health():
    """Expose status of OpenAlgo WebSocket client."""
    from app.core.openalgo_bridge import openalgo_client, FeedState
    status = openalgo_client.get_status()
    
    return {
        "status": "healthy" if status["feed_state"] == FeedState.HEALTHY.value else "degraded" if status["feed_state"] == FeedState.DEGRADED.value else "down",
        "details": status
    }
