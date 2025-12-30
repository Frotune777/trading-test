from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps import get_db
from app.core.redis import redis_client

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

@router.get("/health/system", tags=["health"])
async def system_health(db: Session = Depends(get_db)):
    health = {"database": "unknown", "redis": "unknown"}
    
    # DB Check
    try:
        db.execute(text("SELECT 1"))
        health["database"] = "connected"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        
    # Redis Check
    if redis_client:
        try:
            await redis_client.ping()
            health["redis"] = "connected"
        except Exception as e:
            health["redis"] = f"error: {str(e)}"
    else:
        health["redis"] = "unavailable"
        
    return health
