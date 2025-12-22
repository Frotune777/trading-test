import sys
import os
import asyncio
from httpx import AsyncClient, ASGITransport

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.main import app

async def test_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        print("\n--- Testing Health Check ---")
        response = await ac.get("/api/v1/health")
        print(f"Health Check: {response.status_code} - {response.json()}")

        print("\n--- Testing Stocks List (Data API) ---")
        response = await ac.get("/api/v1/data/stocks")
        print(f"Stocks List: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Count: {data.get('count', 0)}")
            if data.get('symbols'):
                print(f"Sample Symbols: {data['symbols'][:5]}")

        print("\n--- Testing Market Indices ---")
        response = await ac.get("/api/v1/market/indices")
        print(f"Market Indices: {response.status_code}")
        if response.status_code == 200:
            print(f"Results: {len(response.json().get('data', []))} indices found.")

        print("\n--- Testing Technical Indicators (RELIANCE) ---")
        response = await ac.get("/api/v1/technicals/indicators/RELIANCE")
        print(f"Technicals: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Indicators for {data.get('symbol')}: {len(data.get('indicators', []))} records.")
        else:
            print(f"Error: {response.text}")
            
        print("\n--- Testing Option Chain (NIFTY) ---")
        response = await ac.get("/api/v1/derivatives/option-chain/NIFTY")
        print(f"Option Chain: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Records for {data.get('symbol')}: {data.get('count', 0)}")
        else:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
