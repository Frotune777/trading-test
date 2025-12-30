import asyncio
import logging
from app.core.database import SessionLocal
from app.services.ta_aggregator import TAggregator
from app.database.models_quad import QUADUserPreferences

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_ta_aggregator():
    async with SessionLocal() as db:
        aggregator = TAggregator(db)
        
        print("\n--- Verifying TA Weights ---")
        # Try to update weights
        weights = {"trend": 0.4, "momentum": 0.3, "volatility": 0.2, "volume": 0.1}
        success = await aggregator.update_regime_weights("TRENDING_UP", weights)
        print(f"Update weights: {'✅' if success else '❌'}")
        
        # Try to load weights
        loaded = await aggregator._load_regime_weights("TRENDING_UP")
        print(f"Loaded weights: {loaded}")
        
        print("\n--- Verifying Accuracy Calculation ---")
        accuracy = await aggregator.get_historical_accuracy(30)
        print(f"Accuracy metrics: {accuracy}")
        
        print("\n--- Verifying Performance Metrics ---")
        performance = await aggregator.get_indicator_performance()
        print(f"Performance metrics: {performance}")
        
        print("\n✅ Verification complete")

if __name__ == "__main__":
    asyncio.run(verify_ta_aggregator())
