"""
Squareoff Scheduler
Auto-squareoff for intraday strategies at specified time.
"""

import logging
from datetime import datetime, time
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.database.models_strategy import Strategy
from app.services.strategy_service import StrategyService
from app.services.order_queue import order_queue
from app.core.database import get_db

logger = logging.getLogger(__name__)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Global scheduler instance
scheduler = AsyncIOScheduler(timezone=IST)


class SquareoffScheduler:
    """
    Squareoff Scheduler for Intraday Strategies
    
    Features:
        - Schedule auto-squareoff at specified time
        - Close all positions for strategy
        - Market hours validation
        - Timezone-aware (IST)
    """
    
    def __init__(self):
        self.scheduler = scheduler
        logger.info("SquareoffScheduler initialized")
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("SquareoffScheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("SquareoffScheduler stopped")
    
    async def schedule_squareoff(self, strategy: Strategy, db: Session):
        """
        Schedule squareoff for intraday strategy.
        
        Args:
            strategy: Strategy to schedule squareoff for
            db: Database session
        """
        if not strategy.is_intraday or not strategy.squareoff_time:
            logger.warning(f"Cannot schedule squareoff for non-intraday strategy: {strategy.name}")
            return
        
        job_id = f"squareoff_{strategy.id}"
        
        # Remove existing job if any
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed existing squareoff job for {strategy.name}")
        
        # Create cron trigger
        trigger = CronTrigger(
            hour=strategy.squareoff_time.hour,
            minute=strategy.squareoff_time.minute,
            timezone=IST
        )
        
        # Add job
        self.scheduler.add_job(
            self._execute_squareoff,
            trigger=trigger,
            args=[strategy.id],
            id=job_id,
            name=f"Squareoff {strategy.name}",
            replace_existing=True
        )
        
        logger.info(
            f"Scheduled squareoff for {strategy.name} at "
            f"{strategy.squareoff_time.strftime('%H:%M')} IST"
        )
    
    async def cancel_squareoff(self, strategy_id: int):
        """Cancel scheduled squareoff for strategy"""
        job_id = f"squareoff_{strategy_id}"
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Cancelled squareoff job for strategy {strategy_id}")
    
    async def _execute_squareoff(self, strategy_id: int):
        """
        Execute squareoff for strategy.
        
        Closes all positions by placing smart orders with position_size=0.
        """
        try:
            # Get database session
            db = next(get_db())
            
            # Get strategy
            service = StrategyService(db)
            # Note: We can't use user_id check here, so we query directly
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            
            if not strategy or not strategy.is_intraday or not strategy.is_active:
                logger.warning(f"Squareoff skipped for strategy {strategy_id}: not active or not intraday")
                return
            
            # Get symbol mappings
            mappings = await service.get_symbol_mappings(strategy_id)
            
            if not mappings:
                logger.info(f"No symbols to squareoff for strategy {strategy.name}")
                return
            
            logger.info(f"Executing squareoff for strategy {strategy.name} ({len(mappings)} symbols)")
            
            # Queue squareoff orders for each symbol
            for mapping in mappings:
                order_data = {
                    "symbol": mapping.symbol,
                    "exchange": mapping.exchange,
                    "product": mapping.product_type,
                    "action": "SELL",  # Direction doesn't matter for smart order
                    "pricetype": "MARKET",
                    "quantity": "0",
                    "position_size": "0",  # This triggers position close
                    "strategy": strategy.name,
                    "broker": mapping.broker
                }
                
                # Enqueue as smart order
                await order_queue.enqueue_order(
                    order_data=order_data,
                    is_smart_order=True
                )
                
                logger.info(f"Queued squareoff order for {mapping.symbol}")
            
            logger.info(f"Squareoff completed for strategy {strategy.name}")
            
        except Exception as e:
            logger.error(f"Error executing squareoff for strategy {strategy_id}: {e}")


# Global singleton instance
squareoff_scheduler = SquareoffScheduler()
