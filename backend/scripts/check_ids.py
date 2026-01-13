import asyncio
from sqlalchemy import text
from app.core.database import SessionLocal

async def check_ids():
    async with SessionLocal() as db:
        print("--- Checking IDs ---")
        ids = [572888, 670646, 572889]
        query = text(f"SELECT id, symbol, timestamp FROM historical_ohlc WHERE id = ANY(:ids)")
        result = await db.execute(query, {"ids": ids})
        rows = result.fetchall()
        for row in rows:
            print(f"Found ID: {row[0]}, TS: {row[2]}")

if __name__ == "__main__":
    asyncio.run(check_ids())
