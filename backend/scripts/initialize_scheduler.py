"""
Initialize Scheduler with Default Jobs
Sets up data collection jobs for NIFTY 50 stocks
"""

import asyncio
import logging
from app.core.scheduler_config import scheduler_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Top 50 NIFTY stocks
NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
    "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA",
    "TITAN", "ULTRACEMCO", "BAJFINANCE", "NESTLEIND", "WIPRO",
    "HCLTECH", "ONGC", "NTPC", "POWERGRID", "M&M",
    "TATAMOTORS", "TATASTEEL", "TECHM", "ADANIENT", "COALINDIA",
    "JSWSTEEL", "INDUSINDBK", "BAJAJFINSV", "GRASIM", "HINDALCO",
    "DRREDDY", "CIPLA", "EICHERMOT", "BRITANNIA", "DIVISLAB",
    "APOLLOHOSP", "BPCL", "TATACONSUM", "HEROMOTOCO", "SHRIRAMFIN",
    "SBILIFE", "ADANIPORTS", "LTIM", "BAJAJ-AUTO", "HDFCLIFE"
]


async def initialize_scheduler():
    """Initialize scheduler with default jobs"""
    
    logger.info("=" * 60)
    logger.info("INITIALIZING SCHEDULER WITH DEFAULT JOBS")
    logger.info("=" * 60)
    
    # 1. Schedule market close download (3:35 PM IST daily)
    logger.info(f"\n1. Scheduling market close download for {len(NIFTY_50_SYMBOLS)} symbols...")
    job_id_1 = scheduler_config.schedule_market_close_download(
        symbols=NIFTY_50_SYMBOLS,
        intervals=["1m", "5m", "15m", "1h", "1d"],
        enabled=True
    )
    logger.info(f"   ✅ Created job: {job_id_1}")
    
    # 2. Schedule pre-market download (8:30 AM IST daily)
    logger.info(f"\n2. Scheduling pre-market download for {len(NIFTY_50_SYMBOLS)} symbols...")
    job_id_2 = scheduler_config.schedule_pre_market_download(
        symbols=NIFTY_50_SYMBOLS,
        enabled=True
    )
    logger.info(f"   ✅ Created job: {job_id_2}")
    
    # 3. Schedule intraday LTP refresh (every 5 minutes during market hours)
    logger.info(f"\n3. Scheduling intraday LTP refresh for {len(NIFTY_50_SYMBOLS)} symbols...")
    job_id_3 = scheduler_config.schedule_intraday_ltp_refresh(
        symbols=NIFTY_50_SYMBOLS,
        interval_minutes=5,
        enabled=True
    )
    logger.info(f"   ✅ Created job: {job_id_3}")
    
    # 4. Schedule QUAD analysis (9:30 AM, 12 PM, 3 PM IST)
    logger.info(f"\n4. Scheduling QUAD analysis for {len(NIFTY_50_SYMBOLS)} symbols...")
    job_id_4 = scheduler_config.schedule_quad_analysis(
        symbols=NIFTY_50_SYMBOLS,
        enabled=True
    )
    logger.info(f"   ✅ Created job: {job_id_4}")
    
    # Display all jobs
    logger.info("\n" + "=" * 60)
    logger.info("SCHEDULED JOBS SUMMARY")
    logger.info("=" * 60)
    
    all_jobs = scheduler_config.get_all_jobs()
    for job in all_jobs:
        logger.info(f"\n📅 {job['name']}")
        logger.info(f"   ID: {job['id']}")
        logger.info(f"   Schedule: {job['schedule']}")
        logger.info(f"   Symbols: {job['symbols_count']}")
        logger.info(f"   Enabled: {job['enabled']}")
        logger.info(f"   Next Run: {job['next_run_time']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ SCHEDULER INITIALIZATION COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    # Start scheduler first
    scheduler_config.start()
    
    # Initialize jobs
    asyncio.run(initialize_scheduler())
    
    # Keep running
    logger.info("\nScheduler is now running. Press Ctrl+C to stop.")
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logger.info("\nShutting down scheduler...")
        scheduler_config.stop()
