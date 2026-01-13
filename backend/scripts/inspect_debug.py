import asyncio
from sqlalchemy import text
from app.core.database import SessionLocal

async def inspect_reliance():
    async with SessionLocal() as db:
        print("--- Inspecting RELIANCE Data for 2026-01-06 ---")
        query = text("""
            SELECT id, symbol, exchange, interval, timestamp, open, close
            FROM historical_ohlc
            WHERE symbol = 'RELIANCE'
            AND timestamp >= '2026-01-05'
            AND timestamp <= '2026-01-07'
            ORDER BY timestamp
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        for row in rows:
            print(f"ID: {row[0]}, Exch: {row[2]}, Int: {row[3]}, TS: {row[4]}, Open: {row[5]}, Close: {row[6]}")

if __name__ == "__main__":
    asyncio.run(inspect_reliance())
