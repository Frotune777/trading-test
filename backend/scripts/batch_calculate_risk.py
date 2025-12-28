"""
Batch Calculate Risk Metrics for All NIFTY 50 Stocks

Calculates VaR, Beta, Sharpe, and Volatility for all stocks and stores in PostgreSQL.
"""

import sys
sys.path.insert(0, '/app')

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import text
from app.core.config import settings
from app.services.risk_metrics_service import RiskMetricsService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# NIFTY 50 symbols
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


async def batch_calculate_risk_metrics():
    """Calculate and store risk metrics for all NIFTY 50 stocks"""
    logger.info("Initializing Risk Metrics Service...")
    
    # Create PostgreSQL engine
    pg_uri = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_SERVER}:5432/{settings.POSTGRES_DB}"
    )
    engine = create_async_engine(pg_uri, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    successful = 0
    failed = 0
    
    logger.info("=" * 60)
    logger.info("BATCH RISK METRICS CALCULATION")
    logger.info("=" * 60)
    logger.info(f"Symbols: {len(NIFTY_50_SYMBOLS)}")
    logger.info("")
    
    async with session_maker() as session:
        risk_service = RiskMetricsService(session)
        
        for i, symbol in enumerate(NIFTY_50_SYMBOLS, 1):
            logger.info(f"[{i}/{len(NIFTY_50_SYMBOLS)}] Calculating risk metrics for {symbol}...")
            
            try:
                metrics = await risk_service.calculate_all_metrics(symbol)
                if metrics:
                    logger.info(f"  ✅ {symbol}: VaR 95% = {metrics.var_95_30d:.2f}%, Beta = {metrics.beta_252d if metrics.beta_252d else 'N/A'}")
                    successful += 1
                else:
                    logger.warning(f"  ❌ {symbol}: Calculation failed")
                    failed += 1
            except Exception as e:
                logger.error(f"  ❌ {symbol}: Error: {e}")
                failed += 1
                
            # commit after each symbol
            await session.commit()
            
    logger.info("")
    logger.info("=" * 60)
    logger.info("CALCULATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total symbols: {len(NIFTY_50_SYMBOLS)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info("")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(batch_calculate_risk_metrics())
