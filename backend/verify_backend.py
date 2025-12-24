import asyncio
import httpx
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"
SYMBOL = "RELIANCE"

async def check_endpoint(client, url, name):
    start = time.time()
    try:
        response = await client.get(url)
        duration = time.time() - start
        
        if response.status_code == 200:
            print(f"✅ {name}: Success ({duration:.3f}s)")
            return True, duration
        else:
            print(f"❌ {name}: Failed ({response.status_code}) - {response.text}")
            return False, duration
    except Exception as e:
        print(f"❌ {name}: Error - {str(e)}")
        return False, 0

async def main():
    print("🚀 Starting Backend Verification...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health/Root Check (Assuming /docs or similar works, or we check a known good endpoint)
        # Verify Market Breadth
        print("\n--- Market Data ---")
        await check_endpoint(client, f"{BASE_URL}/market/breadth", "Market Breadth")
        
        # 2. Derivatives
        print("\n--- Derivatives ---")
        await check_endpoint(client, f"{BASE_URL}/derivatives/option-chain/{SYMBOL}", f"Option Chain ({SYMBOL})")
        
        # 3. Technicals (Performance Check)
        print("\n--- Technicals ---")
        print(f"Testing Intraday Data for {SYMBOL}...")
        success, duration = await check_endpoint(client, f"{BASE_URL}/technicals/intraday/{SYMBOL}?interval=5m", "Intraday Data")
        
        if success and duration > 1.0:
            print(f"⚠️  Performance Warning: Intraday data took {duration:.3f}s (Threshold: 1.0s)")
        
        # Test Indicators
        await check_endpoint(client, f"{BASE_URL}/technicals/indicators/{SYMBOL}", "Technical Indicators")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAborted.")
