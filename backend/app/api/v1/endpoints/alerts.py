# app/api/v1/endpoints/alerts.py

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.services.alert_service import AlertService

router = APIRouter()
alert_service = AlertService()

@router.get("/recent", response_model=List[Dict[str, Any]])
async def get_recent_alerts(limit: int = 50):
    """
    Fetch the latest system alerts.
    """
    try:
        return alert_service.get_latest_alerts(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
