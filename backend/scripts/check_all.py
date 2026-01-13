import asyncio
from sqlalchemy import text
from app.core.database import SessionLocal

async def check_all_reliance():
    async with SessionLocal() as db:
        print("--- ALL RELIANCE Records for Jan 6 ---")
        
        # Check raw dates
        query = text("""
            SELECT id, symbol, timestamp, date(timestamp)
            FROM historical_ohlc
            WHERE symbol = 'RELIANCE'
            AND interval = '1d'
            AND exchange = 'NSE'
            AND timestamp >= '2026-01-05 00:00:00'
            AND timestamp <= '2026-01-07 23:59:59'
            ORDER BY timestamp
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, TS: {row[2]}, Date: {row[3]}")

if __name__ == "__main__":
    asyncio.run(check_all_reliance())
