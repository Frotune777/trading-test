"""
Create all QUAD tables and calculate risk metrics
"""
import asyncio
import sys
sys.path.insert(0, '/home/fortune/Desktop/Python_Projects/quad_trading/trading-test/backend')

from sqlalchemy import text
from app.core.database import async_engine
from app.database.models_quad import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_tables_and_calculate():
    """Create all QUAD tables and calculate risk metrics"""
    
    # Create all tables
    logger.info("Creating QUAD tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ All QUAD tables created")
    
    # Now run the risk metrics calculation
    logger.info("\nCalculating risk metrics...")
    from scripts.calculate_risk_metrics import calculate_risk_metrics
    await calculate_risk_metrics()

if __name__ == "__main__":
    asyncio.run(create_tables_and_calculate())
