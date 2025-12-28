"""
Script to simulate historical decisions and evaluate their accuracy.
This script populates the database with historical QUAD decisions and evaluations
using existing price history.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import text
from app.core.database import SessionLocal
from app.database.models_quad import QUADDecision, QUADSignalAccuracy
from app.services.quad_analytics_service import QUADAnalyticsService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simulate_historical_data():
    async with SessionLocal() as db:
        symbol = "RELIANCE"
        analytics_service = QUADAnalyticsService(db)
        
        # 1. Fetch some historical dates from price_history
        result = await db.execute(
            text("""
                SELECT date, close
                FROM price_history
                WHERE symbol = :symbol
                ORDER BY date DESC
                OFFSET 10
                LIMIT 20
            """),
            {"symbol": symbol}
        )
        rows = result.fetchall()
        
        if not rows:
            logger.error(f"No price history found for {symbol}")
            return
            
        logger.info(f"Faked {len(rows)} historical decisions for {symbol}")
        
        import random
        
        for date, close in rows:
            # Create a fake decision
            signal = random.choice(["BUY", "SELL", "HOLD"])
            conviction = random.randint(60, 95)
            
            decision = QUADDecision(
                symbol=symbol,
                timestamp=date,
                conviction=conviction,
                signal=signal,
                trend_score=random.randint(40, 100),
                momentum_score=random.randint(40, 100),
                volatility_score=random.randint(40, 100),
                liquidity_score=random.randint(40, 100),
                sentiment_score=random.randint(40, 100),
                regime_score=random.randint(40, 100),
                reasoning_summary=f"Simulated {signal} signal for testing accuracy.",
                current_price=close,
                volume=0
            )
            db.add(decision)
            
        await db.commit()
        
        # 2. Evaluate them
        logger.info(f"Evaluating simulated decisions for {symbol}...")
        results = await analytics_service.evaluate_decisions(symbol, evaluation_window_days=5)
        logger.info(f"Evaluation Results: {results}")

if __name__ == "__main__":
    asyncio.run(simulate_historical_data())
