from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.redis import redis_client
from datetime import datetime
import time

router = APIRouter()

@router.get("/health", tags=["health"])
async def health_check(db: Session = Depends(get_db)):
    """Main health check - database connectivity"""
    start = time.time()
    try:
        await db.execute(text("SELECT 1"))
        latency = int((time.time() - start) * 1000)
        return {
            "status": "healthy",
            "version": "1.0.0-QUAD",
            "latency_ms": latency,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "down",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/health/openalgo", tags=["health"])
@router.get("/openalgo/health", tags=["health"])
async def openalgo_health():
    """Expose status of OpenAlgo WebSocket client."""
    start = time.time()
    try:
        from app.core.openalgo_bridge import openalgo_client, FeedState
        status = openalgo_client.get_status()
        latency = int((time.time() - start) * 1000)
        
        feed_state = status.get("feed_state", "UNKNOWN")
        
        return {
            "status": "healthy" if feed_state == FeedState.HEALTHY.value else "degraded" if feed_state == FeedState.DEGRADED.value else "down",
            "latency_ms": latency,
            "details": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "down",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/health/nse", tags=["health"])
async def nse_health():
    """Check NSE historical data availability"""
    start = time.time()
    try:
        # Simple check - try to import NSE module
        from app.services.nse_data_service import NSEDataService
        latency = int((time.time() - start) * 1000)
        
        return {
            "status": "healthy",
            "message": "NSE historical data service available",
            "latency_ms": latency,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "message": f"NSE service error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/health/redis", tags=["health"])
async def redis_health():
    """Check Redis cache connectivity"""
    start = time.time()
    try:
        if redis_client:
            await redis_client.ping()
            latency = int((time.time() - start) * 1000)
            return {
                "status": "healthy",
                "message": "Redis cache operational",
                "latency_ms": latency,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "degraded",
                "message": "Redis client not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "down",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/health/datasources", tags=["health"])
async def datasources_health(db: Session = Depends(get_db)):
    """Aggregated health check for all data sources"""
    sources = []
    overall_status = "healthy"
    
    # Check OpenAlgo
    try:
        from app.core.openalgo_bridge import openalgo_client, FeedState
        status = openalgo_client.get_status()
        feed_state = status.get("feed_state", "UNKNOWN")
        
        openalgo_status = "healthy" if feed_state == FeedState.HEALTHY.value else "degraded" if feed_state == FeedState.DEGRADED.value else "down"
        sources.append({
            "name": "OpenAlgo (Live Market Data)",
            "status": openalgo_status,
            "message": "Real-time feed active" if openalgo_status == "healthy" else "Connection issues",
            "lastUpdate": datetime.utcnow().isoformat()
        })
        if openalgo_status == "down":
            overall_status = "critical"
        elif openalgo_status == "degraded" and overall_status == "healthy":
            overall_status = "degraded"
    except Exception as e:
        sources.append({
            "name": "OpenAlgo (Live Market Data)",
            "status": "down",
            "message": f"Service error: {str(e)}",
            "lastUpdate": datetime.utcnow().isoformat()
        })
        overall_status = "critical"
    
    # Check NSE
    try:
        from app.services.nse_data_service import NSEDataService
        sources.append({
            "name": "NSE Historical Data",
            "status": "healthy",
            "message": "Historical data available",
            "lastUpdate": datetime.utcnow().isoformat()
        })
    except Exception as e:
        sources.append({
            "name": "NSE Historical Data",
            "status": "degraded",
            "message": "Limited availability",
            "lastUpdate": datetime.utcnow().isoformat()
        })
        if overall_status == "healthy":
            overall_status = "degraded"
    
    # Check PostgreSQL
    start = time.time()
    try:
        db.execute(text("SELECT 1"))
        latency = int((time.time() - start) * 1000)
        sources.append({
            "name": "PostgreSQL Database",
            "status": "healthy",
            "message": "Database operational",
            "latency": latency,
            "lastUpdate": datetime.utcnow().isoformat()
        })
    except Exception as e:
        sources.append({
            "name": "PostgreSQL Database",
            "status": "down",
            "message": f"Connection failed: {str(e)}",
            "lastUpdate": datetime.utcnow().isoformat()
        })
        overall_status = "critical"
    
    # Check Redis
    try:
        if redis_client:
            await redis_client.ping()
            sources.append({
                "name": "Redis Cache",
                "status": "healthy",
                "message": "Cache active",
                "lastUpdate": datetime.utcnow().isoformat()
            })
        else:
            sources.append({
                "name": "Redis Cache",
                "status": "degraded",
                "message": "Cache unavailable",
                "lastUpdate": datetime.utcnow().isoformat()
            })
            if overall_status == "healthy":
                overall_status = "degraded"
    except Exception as e:
        sources.append({
            "name": "Redis Cache",
            "status": "degraded",
            "message": "Cache offline",
            "lastUpdate": datetime.utcnow().isoformat()
        })
        if overall_status == "healthy":
            overall_status = "degraded"
    
    return {
        "sources": sources,
        "overall_status": overall_status,
        "last_check": datetime.utcnow().isoformat()
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
