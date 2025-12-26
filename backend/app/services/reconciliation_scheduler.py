"""
Reconciliation Scheduler
Schedules automatic position reconciliation every 5 minutes.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pytz

from app.services.position_reconciliation import PositionReconciliationService
from app.core.database import get_db

logger = logging.getLogger(__name__)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Global scheduler instance
reconciliation_scheduler = AsyncIOScheduler(timezone=IST)


class ReconciliationScheduler:
    """
    Automatic Position Reconciliation Scheduler
    
    Features:
        - Runs every 5 minutes
        - Only during market hours (9:15 AM - 3:30 PM IST)
        - Auto-detects discrepancies
        - Alerts on mismatches
    """
    
    def __init__(self):
        self.scheduler = reconciliation_scheduler
        self.enabled = True
        logger.info("ReconciliationScheduler initialized")
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            # Add reconciliation job (every 5 minutes)
            self.scheduler.add_job(
                self._run_reconciliation,
                trigger=IntervalTrigger(minutes=5),
                id="position_reconciliation",
                name="Position Reconciliation",
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("ReconciliationScheduler started (every 5 minutes)")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("ReconciliationScheduler stopped")
    
    def pause(self):
        """Pause reconciliation"""
        self.enabled = False
        logger.info("Reconciliation paused")
    
    def resume(self):
        """Resume reconciliation"""
        self.enabled = True
        logger.info("Reconciliation resumed")
    
    async def _run_reconciliation(self):
        """Execute reconciliation job"""
        if not self.enabled:
            logger.debug("Reconciliation skipped (paused)")
            return
        
        # Check if market hours
        from datetime import datetime, time
        now = datetime.now(IST)
        current_time = now.time()
        
        market_open = time(9, 15)
        market_close = time(15, 30)
        
        if not (market_open <= current_time <= market_close):
            logger.debug("Reconciliation skipped (outside market hours)")
            return
        
        try:
            logger.info("Starting scheduled position reconciliation")
            
            # Get database session
            db = next(get_db())
            
            # Run reconciliation
            service = PositionReconciliationService(db)
            run = await service.reconcile_positions()
            
            logger.info(
                f"Scheduled reconciliation completed: "
                f"{run.total_positions} positions, "
                f"{run.discrepancies_found} discrepancies"
            )
            
            # Alert if discrepancies found
            if run.discrepancies_found > 0:
                logger.warning(
                    f"⚠️ Position discrepancies detected: {run.discrepancies_found} mismatches"
                )
                # TODO: Send alert (Telegram, Email, etc.)
            
        except Exception as e:
            logger.error(f"Error in scheduled reconciliation: {e}")


# Global singleton instance
recon_scheduler = ReconciliationScheduler()
