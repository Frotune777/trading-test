"""
Scheduler Configuration for Data Pipeline
Handles automated data fetching at market schedules.
Complies with Rules #1-3 (no execution, no gate bypass).
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, time as dt_time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone

from app.core.config import settings
from app.services.data_pipeline_service import data_pipeline_service
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)

# IST timezone
IST = timezone('Asia/Kolkata')


class SchedulerConfig:
    """
    Manages scheduled data fetching jobs.
    
    Compliance:
        - Rule #1-3: NO execution, NO gate bypass
        - Rule #20: Automation requires alerting, observability, kill switches
        - Rule #44: Agent must not schedule itself to trade
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=IST)
        self.alert_service = AlertService()
        self.jobs: Dict[str, Any] = {}
        self.is_running = False
    
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Data pipeline scheduler STARTED")
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Data pipeline scheduler STOPPED")
    
    def schedule_market_close_download(
        self,
        symbols: List[str],
        intervals: List[str] = ["1m", "5m"],
        enabled: bool = True
    ) -> str:
        """
        Schedule download at market close (3:35 PM IST).
        
        Args:
            symbols: List of symbols to download
            intervals: Data intervals to fetch
            enabled: Whether to enable the job immediately
            
        Returns:
            Job ID
        """
        job_id = "market_close_download"
        
        # Market close is at 3:30 PM, we fetch at 3:35 PM to ensure all data is available
        trigger = CronTrigger(
            hour=15,
            minute=35,
            timezone=IST
        )
        
        async def job_func():
            logger.info(f"Market close download started for {len(symbols)} symbols")
            
            await self.alert_service.emit(
                alert_type="SCHEDULED_DOWNLOAD_START",
                message=f"Market close download started: {len(symbols)} symbols, intervals={intervals}",
                level="INFO"
            )
            
            for interval in intervals:
                result = await data_pipeline_service.fetch_historical_batch(
                    symbols=symbols,
                    interval=interval,
                    period="1d"  # Just today's data
                )
                
                logger.info(
                    f"Market close download ({interval}): "
                    f"{result['successful']}/{result['total']} successful"
                )
            
            await self.alert_service.emit(
                alert_type="SCHEDULED_DOWNLOAD_COMPLETE",
                message=f"Market close download completed",
                level="INFO"
            )
        
        job = self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            name="Market Close Download",
            replace_existing=True
        )
        
        if not enabled:
            job.pause()
        
        self.jobs[job_id] = {
            "id": job_id,
            "name": "Market Close Download",
            "schedule": "Daily at 3:35 PM IST",
            "symbols": symbols,
            "intervals": intervals,
            "enabled": enabled
        }
        
        logger.info(f"Scheduled market close download: {len(symbols)} symbols at 3:35 PM IST")
        return job_id
    
    def schedule_pre_market_download(
        self,
        symbols: List[str],
        enabled: bool = True
    ) -> str:
        """
        Schedule download before market open (8:30 AM IST).
        Fetches previous day's daily data.
        """
        job_id = "pre_market_download"
        
        trigger = CronTrigger(
            hour=8,
            minute=30,
            timezone=IST
        )
        
        async def job_func():
            logger.info(f"Pre-market download started for {len(symbols)} symbols")
            
            await self.alert_service.emit(
                alert_type="SCHEDULED_DOWNLOAD_START",
                message=f"Pre-market download started: {len(symbols)} symbols",
                level="INFO"
            )
            
            result = await data_pipeline_service.fetch_historical_batch(
                symbols=symbols,
                interval="1d",
                period="5d"  # Last 5 days
            )
            
            logger.info(
                f"Pre-market download: {result['successful']}/{result['total']} successful"
            )
            
            await self.alert_service.emit(
                alert_type="SCHEDULED_DOWNLOAD_COMPLETE",
                message=f"Pre-market download completed: {result['successful']}/{result['total']} successful",
                level="INFO"
            )
        
        job = self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            name="Pre-Market Download",
            replace_existing=True
        )
        
        if not enabled:
            job.pause()
        
        self.jobs[job_id] = {
            "id": job_id,
            "name": "Pre-Market Download",
            "schedule": "Daily at 8:30 AM IST",
            "symbols": symbols,
            "enabled": enabled
        }
        
        logger.info(f"Scheduled pre-market download: {len(symbols)} symbols at 8:30 AM IST")
        return job_id
    
    def schedule_intraday_ltp_refresh(
        self,
        symbols: List[str],
        interval_minutes: int = 5,
        enabled: bool = True
    ) -> str:
        """
        Schedule periodic LTP refresh during market hours.
        
        Args:
            symbols: Symbols to refresh
            interval_minutes: Refresh interval in minutes
            enabled: Whether to enable immediately
        """
        job_id = "intraday_ltp_refresh"
        
        # Only run during market hours (9:15 AM - 3:30 PM IST)
        trigger = IntervalTrigger(
            minutes=interval_minutes,
            timezone=IST
        )
        
        async def job_func():
            # Check if market is open
            now = datetime.now(IST)
            market_open = dt_time(9, 15)
            market_close = dt_time(15, 30)
            
            if not (market_open <= now.time() <= market_close):
                logger.debug("Skipping LTP refresh - market closed")
                return
            
            # Skip weekends
            if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                logger.debug("Skipping LTP refresh - weekend")
                return
            
            logger.debug(f"LTP refresh started for {len(symbols)} symbols")
            
            success_count = 0
            for symbol in symbols:
                success = await data_pipeline_service.fetch_and_cache_ltp(symbol)
                if success:
                    success_count += 1
            
            logger.info(f"LTP refresh: {success_count}/{len(symbols)} successful")
        
        job = self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            name="Intraday LTP Refresh",
            replace_existing=True
        )
        
        if not enabled:
            job.pause()
        
        self.jobs[job_id] = {
            "id": job_id,
            "name": "Intraday LTP Refresh",
            "schedule": f"Every {interval_minutes} minutes (market hours only)",
            "symbols": symbols,
            "enabled": enabled
        }
        
        logger.info(f"Scheduled intraday LTP refresh: every {interval_minutes} minutes")
        return job_id
    
    def schedule_quad_analysis(
        self,
        symbols: List[str],
        enabled: bool = True
    ) -> str:
        """
        Schedule QUAD analysis at key market intervals.
        
        Runs at:
        - 9:30 AM IST (30 min after market open)
        - 12:00 PM IST (mid-day)
        - 3:00 PM IST (30 min before market close)
        
        Args:
            symbols: List of symbols to analyze
            enabled: Whether to enable the job immediately
            
        Returns:
            Job ID
        """
        job_id = "quad_analysis_scheduled"
        
        # Run at 9:30 AM, 12:00 PM, and 3:00 PM IST
        trigger = CronTrigger(
            hour='9,12,15',
            minute='30,0,0',
            timezone=IST
        )
        
        async def job_func():
            from app.core.database import async_session_maker
            from app.services.quad_analysis_engine import QUADAnalysisEngine
            
            logger.info(f"Scheduled QUAD analysis started for {len(symbols)} symbols")
            
            await self.alert_service.emit(
                alert_type="QUAD_ANALYSIS_START",
                message=f"Scheduled QUAD analysis started: {len(symbols)} symbols",
                level="INFO"
            )
            
            async with async_session_maker() as db:
                engine = QUADAnalysisEngine(db)
                
                try:
                    decisions = await engine.analyze_watchlist(symbols)
                    
                    logger.info(
                        f"Scheduled QUAD analysis complete: "
                        f"{len(decisions)}/{len(symbols)} successful"
                    )
                    
                    await self.alert_service.emit(
                        alert_type="QUAD_ANALYSIS_COMPLETE",
                        message=f"QUAD analysis completed: {len(decisions)}/{len(symbols)} successful",
                        level="INFO"
                    )
                    
                except Exception as e:
                    logger.error(f"Scheduled QUAD analysis failed: {e}", exc_info=True)
                    await self.alert_service.emit(
                        alert_type="QUAD_ANALYSIS_ERROR",
                        message=f"QUAD analysis failed: {str(e)}",
                        level="ERROR"
                    )
        
        job = self.scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            name="QUAD Analysis",
            replace_existing=True
        )
        
        if not enabled:
            job.pause()
        
        self.jobs[job_id] = {
            "id": job_id,
            "name": "QUAD Analysis",
            "schedule": "9:30 AM, 12:00 PM, 3:00 PM IST",
            "symbols": symbols,
            "enabled": enabled
        }
        
        logger.info(f"Scheduled QUAD analysis: {len(symbols)} symbols at 9:30 AM, 12 PM, 3 PM IST")
        return job_id
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.pause()
                if job_id in self.jobs:
                    self.jobs[job_id]["enabled"] = False
                logger.info(f"Job paused: {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.resume()
                if job_id in self.jobs:
                    self.jobs[job_id]["enabled"] = True
                logger.info(f"Job resumed: {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            return False
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"Job deleted: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            return False
    
    def run_job_now(self, job_id: str) -> bool:
        """Run a job immediately (outside its schedule)"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now(IST))
                logger.info(f"Job triggered immediately: {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error running job {job_id}: {e}")
            return False
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all scheduled jobs with their status"""
        jobs_list = []
        
        for job in self.scheduler.get_jobs():
            job_info = self.jobs.get(job.id, {})
            jobs_list.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "enabled": not job.pending,
                "schedule": job_info.get("schedule", "Unknown"),
                "symbols_count": len(job_info.get("symbols", [])),
                "intervals": job_info.get("intervals", [])
            })
        
        return jobs_list


# Global instance
scheduler_config = SchedulerConfig()
