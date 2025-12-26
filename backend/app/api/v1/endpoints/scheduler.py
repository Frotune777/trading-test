"""
Scheduler Management API Endpoints
Provides control over scheduled data fetching jobs.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from app.core.scheduler_config import scheduler_config

logger = logging.getLogger(__name__)

router = APIRouter()


class ScheduleJobRequest(BaseModel):
    """Request model for creating scheduled jobs"""
    job_type: str  # "market_close", "pre_market", "intraday_ltp"
    symbols: List[str]
    intervals: Optional[List[str]] = ["1m", "5m"]
    interval_minutes: Optional[int] = 5
    enabled: bool = True


@router.get("/jobs", response_model=List[Dict[str, Any]])
async def get_all_jobs():
    """
    Get all scheduled jobs.
    
    Returns:
        List of all scheduled jobs with their status
    """
    try:
        jobs = scheduler_config.get_all_jobs()
        return jobs
    except Exception as e:
        logger.error(f"Error getting scheduled jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs", response_model=Dict[str, Any])
async def create_job(request: ScheduleJobRequest):
    """
    Create a new scheduled job.
    
    Args:
        request: Job configuration
        
    Returns:
        Created job details
    """
    try:
        if request.job_type == "market_close":
            job_id = scheduler_config.schedule_market_close_download(
                symbols=request.symbols,
                intervals=request.intervals,
                enabled=request.enabled
            )
        elif request.job_type == "pre_market":
            job_id = scheduler_config.schedule_pre_market_download(
                symbols=request.symbols,
                enabled=request.enabled
            )
        elif request.job_type == "intraday_ltp":
            job_id = scheduler_config.schedule_intraday_ltp_refresh(
                symbols=request.symbols,
                interval_minutes=request.interval_minutes,
                enabled=request.enabled
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown job type: {request.job_type}"
            )
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"Job '{job_id}' created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """
    Pause a scheduled job.
    
    Args:
        job_id: ID of the job to pause
        
    Returns:
        Success message
    """
    try:
        success = scheduler_config.pause_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        
        return {
            "success": True,
            "message": f"Job '{job_id}' paused successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """
    Resume a paused job.
    
    Args:
        job_id: ID of the job to resume
        
    Returns:
        Success message
    """
    try:
        success = scheduler_config.resume_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        
        return {
            "success": True,
            "message": f"Job '{job_id}' resumed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a scheduled job.
    
    Args:
        job_id: ID of the job to delete
        
    Returns:
        Success message
    """
    try:
        success = scheduler_config.delete_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        
        return {
            "success": True,
            "message": f"Job '{job_id}' deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/run")
async def run_job_now(job_id: str):
    """
    Run a job immediately (outside its schedule).
    
    Args:
        job_id: ID of the job to run
        
    Returns:
        Success message
    """
    try:
        success = scheduler_config.run_job_now(job_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        
        return {
            "success": True,
            "message": f"Job '{job_id}' triggered successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_scheduler():
    """
    Start the scheduler.
    
    Returns:
        Success message
    """
    try:
        scheduler_config.start()
        return {
            "success": True,
            "message": "Scheduler started successfully"
        }
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_scheduler():
    """
    Stop the scheduler.
    
    Returns:
        Success message
    """
    try:
        scheduler_config.stop()
        return {
            "success": True,
            "message": "Scheduler stopped successfully"
        }
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
