# app/api/v1/endpoints/execution.py

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import logging
from app.core.config import settings
from app.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

router = APIRouter()
db = DatabaseManager()

@router.get("/status", response_model=Dict[str, Any])
async def get_execution_status() -> Dict[str, Any]:
    """
    Expose current execution state and last activity.
    """
    from app.core.redis import redis_client
    try:
        last_exec = db.get_last_execution()
        
        # Check runtime override
        runtime_enabled = await redis_client.get("runtime:execution_enabled")
        if runtime_enabled is not None:
            effective_enabled = runtime_enabled.decode() == "true"
            is_overridden = True
        else:
            effective_enabled = settings.EXECUTION_ENABLED
            is_overridden = False
            
        return {
            "execution_mode": settings.EXECUTION_MODE,
            "execution_enabled": effective_enabled,
            "is_runtime_overridden": is_overridden,
            "config_enabled": settings.EXECUTION_ENABLED,
            "last_execution_time": last_exec["created_at"] if last_exec else None,
            "last_symbol": last_exec["symbol"] if last_exec else None,
            "last_block_reason": last_exec["execution_block_reason"] if last_exec and last_exec["execution_status"] == "BLOCKED" else None,
            "last_execution_status": last_exec["execution_status"] if last_exec else "NONE",
            "last_order_id": last_exec["order_id"] if last_exec else None
        }
    except Exception as e:
        logger.error(f"Error fetching execution status: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch execution status")

@router.post("/enable")
async def enable_execution():
    """Runtime enable execution via Redis override."""
    from app.core.redis import redis_client
    await redis_client.set("runtime:execution_enabled", "true")
    logger.warning("🚀 EXECUTION ENABLED via runtime override")
    return {"status": "success", "message": "Execution enabled via runtime override"}

@router.post("/disable")
async def disable_execution():
    """Runtime disable execution (Kill Switch) via Redis override."""
    from app.core.redis import redis_client
    await redis_client.set("runtime:execution_enabled", "false")
    logger.warning("🛑 EXECUTION DISABLED via runtime override")
    return {"status": "success", "message": "Execution disabled via runtime override"}
