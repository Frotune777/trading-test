"""
QUAD Scheduler Management API
Endpoints to configure and manage scheduled QUAD analysis
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.scheduler_config import scheduler_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quad/scheduler", tags=["QUAD Scheduler"])


# Request/Response Models
class ScheduleConfigRequest(BaseModel):
    """Request model for configuring scheduled analysis"""
    symbols: List[str]
    enabled: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbols": ["RELIANCE", "TCS", "INFY", "HDFCBANK", "WIPRO"],
                "enabled": True
            }
        }


class ScheduleStatusResponse(BaseModel):
    """Response model for schedule status"""
    job_id: str
    name: str
    schedule: str
    symbols_count: int
    enabled: bool
    next_run_time: str | None


# Endpoints
@router.post("/configure", response_model=dict)
async def configure_quad_schedule(request: ScheduleConfigRequest):
    """
    Configure scheduled QUAD analysis
    
    This endpoint sets up automatic QUAD analysis to run at:
    - 9:30 AM IST (30 min after market open)
    - 12:00 PM IST (mid-day)
    - 3:00 PM IST (30 min before market close)
    
    Args:
        request: Configuration with symbols list and enabled flag
        
    Returns:
        Configuration confirmation
    """
    logger.info(f"Configuring QUAD schedule for {len(request.symbols)} symbols")
    
    try:
        job_id = scheduler_config.schedule_quad_analysis(
            symbols=request.symbols,
            enabled=request.enabled
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"QUAD analysis scheduled for {len(request.symbols)} symbols",
            "schedule": "9:30 AM, 12:00 PM, 3:00 PM IST",
            "symbols": request.symbols,
            "enabled": request.enabled
        }
        
    except Exception as e:
        logger.error(f"Failed to configure QUAD schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure schedule: {str(e)}"
        )


@router.get("/status", response_model=ScheduleStatusResponse)
async def get_schedule_status():
    """
    Get current QUAD analysis schedule status
    
    Returns:
        Current schedule configuration and next run time
    """
    try:
        job = scheduler_config.scheduler.get_job("quad_analysis_scheduled")
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QUAD analysis schedule not configured"
            )
        
        job_info = scheduler_config.jobs.get("quad_analysis_scheduled", {})
        
        return ScheduleStatusResponse(
            job_id=job.id,
            name=job.name,
            schedule=job_info.get("schedule", "Unknown"),
            symbols_count=len(job_info.get("symbols", [])),
            enabled=not job.pending,
            next_run_time=job.next_run_time.isoformat() if job.next_run_time else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schedule status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@router.post("/pause")
async def pause_schedule():
    """
    Pause scheduled QUAD analysis
    
    Returns:
        Confirmation of pause
    """
    try:
        success = scheduler_config.pause_job("quad_analysis_scheduled")
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QUAD analysis schedule not found"
            )
        
        return {
            "success": True,
            "message": "QUAD analysis schedule paused"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause: {str(e)}"
        )


@router.post("/resume")
async def resume_schedule():
    """
    Resume paused QUAD analysis schedule
    
    Returns:
        Confirmation of resume
    """
    try:
        success = scheduler_config.resume_job("quad_analysis_scheduled")
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QUAD analysis schedule not found"
            )
        
        return {
            "success": True,
            "message": "QUAD analysis schedule resumed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume: {str(e)}"
        )


@router.post("/trigger-now")
async def trigger_now():
    """
    Trigger scheduled QUAD analysis immediately (outside schedule)
    
    Returns:
        Confirmation of trigger
    """
    try:
        success = scheduler_config.run_job_now("quad_analysis_scheduled")
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QUAD analysis schedule not configured"
            )
        
        return {
            "success": True,
            "message": "QUAD analysis triggered immediately"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger: {str(e)}"
        )
