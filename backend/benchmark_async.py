import asyncio
import time
import logging
from app.services.reasoning_service import ReasoningService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    service = ReasoningService()
    symbol = "RELIANCE"
    
    print(f"--- Benchmarking Async Analysis (CACHED) for {symbol} ---")
    start = time.perf_counter()
    result = await service.analyze_symbol(symbol)
    end = time.perf_counter()
    
    duration = end - start
    print(f"Total Analysis Time: {duration:.2f}s")
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Directional Bias: {result.get('directional_bias')}")
        
        # In reasoning_service.py, technical_state is returned
        tech_state = result.get('technical_state', {})
        print(f"Technical State Keys: {list(tech_state.keys())}")
        
        # Check weekly SMA
        weekly_sma = tech_state.get('sma_20_weekly')
        print(f"Weekly SMA (20): {weekly_sma}")
        
        # Check daily RSI
        rsi = tech_state.get('rsi')
        print(f"Daily RSI: {rsi}")
        
        # Check if it was built in parallel (log should show timing)
        print(f"Successful Analysis")

if __name__ == "__main__":
    asyncio.run(main())
