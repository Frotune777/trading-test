import asyncio
from sqlalchemy import text
from app.core.database import SessionLocal

async def debug_reliance_grouping():
    async with SessionLocal() as db:
        print("--- Debugging RELIANCE Grouping ---")
        
        # Check raw dates
        query = text("""
            SELECT id, timestamp, date(timestamp) as cast_date
            FROM historical_ohlc
            WHERE symbol = 'RELIANCE'
            AND interval = '1d'
            AND exchange = 'NSE'
            AND timestamp >= '2026-01-06 00:00:00'
            AND timestamp < '2026-01-07 00:00:00'
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, TS: {row[1]}, DateCast: {row[2]}")
            
        # Check grouping count
        group_query = text("""
            SELECT date(timestamp) as day_date, count(*)
            FROM historical_ohlc
            WHERE symbol = 'RELIANCE'
            AND interval = '1d'
            AND exchange = 'NSE'
            AND timestamp >= '2026-01-06 00:00:00'
            AND timestamp < '2026-01-07 00:00:00'
            GROUP BY day_date
        """)
        
        g_result = await db.execute(group_query)
        g_rows = g_result.fetchall()
        print("\nGrouping Result:")
        for row in g_rows:
            print(f"Date: {row[0]}, Count: {row[1]}")

if __name__ == "__main__":
    asyncio.run(debug_reliance_grouping())
