"""
Script to simulate peer decisions for testing PeerComparison component.
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy import text
from app.core.database import SessionLocal
from app.database.models_quad import QUADDecision

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PEERS = ["ONGC", "NTPC", "POWERGRID", "BPCL", "COALINDIA", "RELIANCE"]

async def simulate_peer_data():
    async with SessionLocal() as db:
        import random
        
        for symbol in PEERS:
            # Create a fake decision
            signal = random.choice(["BUY", "SELL", "HOLD"])
            conviction = random.randint(30, 95)
            
            decision = QUADDecision(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                conviction=conviction,
                signal=signal,
                trend_score=random.randint(40, 100),
                momentum_score=random.randint(40, 100),
                volatility_score=random.randint(40, 100),
                liquidity_score=random.randint(40, 100),
                sentiment_score=random.randint(40, 100),
                regime_score=random.randint(40, 100),
                reasoning_summary=f"Simulated {signal} signal for testing peer comparison.",
                current_price=random.randint(100, 3000),
                volume=0
            )
            db.add(decision)
            
        await db.commit()
        logger.info(f"Simulated peer data for {len(PEERS)} symbols.")

if __name__ == "__main__":
    asyncio.run(simulate_peer_data())
