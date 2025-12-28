import asyncio
import sys
import os

# Ensure app can be imported
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.services.risk_metrics_service import RiskMetricsService
from app.database.models_historical import PriceHistory
from sqlalchemy import select

async def main():
    print("🚀 Starting Risk Metrics Calculation for all stocks...")
    
    try:
        async with SessionLocal() as session:
            # Get all symbols from price_history
            result = await session.execute(select(PriceHistory.symbol).distinct())
            symbols = result.scalars().all()
            
            if not symbols:
                print("⚠️  No symbols found in PriceHistory table.")
                return

            print(f"found {len(symbols)} symbols with price history.")
            
            service = RiskMetricsService(session)
            
            success_count = 0
            failure_count = 0
            
            for symbol in symbols:
                print(f"Processing {symbol}...", end="", flush=True)
                metric = await service.calculate_all_metrics(symbol)
                if metric:
                    print(f" ✅ VaR(99%): {metric.var_99_30d:.2f}%")
                    success_count += 1
                else:
                    print(f" ❌ Failed")
                    failure_count += 1
                    
            print(f"\n✨ Completed. Success: {success_count}, Failed: {failure_count}")
            
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
