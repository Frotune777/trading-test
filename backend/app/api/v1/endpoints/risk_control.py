from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.redis import redis_client

router = APIRouter()

class KillSwitchRequest(BaseModel):
    action: str  # "ACTIVATE" or "DEACTIVATE"
    reason: str

@router.post("/kill-switch")
async def toggle_kill_switch(payload: KillSwitchRequest):
    """
    Toggle the Global Kill Switch.
    """
    try:
        key = "risk:kill_switch"
        if payload.action == "ACTIVATE":
            await redis_client.set(key, "active")
            # Log this critical action
            return {"status": "success", "message": "Global Kill Switch ACTIVATED", "reason": payload.reason}
            
        elif payload.action == "DEACTIVATE":
            await redis_client.delete(key)
            return {"status": "success", "message": "Global Kill Switch DEACTIVATED", "reason": payload.reason}
            
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use ACTIVATE or DEACTIVATE.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kill-switch")
async def get_kill_switch_status():
    """Get current Kill Switch status."""
    try:
        status = await redis_client.get("risk:kill_switch")
        is_active = status is not None and status == "active"
        return {"active": is_active}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
