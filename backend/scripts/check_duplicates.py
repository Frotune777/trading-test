import asyncio
from sqlalchemy import text, inspect
from app.core.database import SessionLocal, engine

async def check_duplicates_and_constraints():
    async with SessionLocal() as db:
        print("--- Checking for Duplicates ---")
        # Query to find duplicates
        query = text("""
            SELECT symbol, interval, timestamp, count(*)
            FROM historical_ohlc
            GROUP BY symbol, interval, timestamp
            HAVING count(*) > 1
            LIMIT 20
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        if rows:
            print(f"Found duplicates (showing first 20):")
            for row in rows:
                print(f"Symbol: {row[0]}, Interval: {row[1]}, Time: {row[2]}, Count: {row[3]}")
            
            # Count total duplicates
            count_query = text("""
                SELECT count(*) FROM (
                    SELECT symbol, interval, timestamp
                    FROM historical_ohlc
                    GROUP BY symbol, interval, timestamp
                    HAVING count(*) > 1
                ) as sub
            """)
            total_dups = await db.execute(count_query)
            print(f"\nTotal groups with duplicates: {total_dups.scalar()}")
        else:
            print("No duplicates found based on (symbol, interval, timestamp).")

    print("\n--- Checking Indices and Constraints ---")
    # We need a synchronous connection to use inspect properly with some drivers, 
    # but let's try raw SQL for postgres to list indices which covers constraints too
    async with SessionLocal() as db:
        idx_query = text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'historical_ohlc';
        """)
        idx_result = await db.execute(idx_query)
        idxs = idx_result.fetchall()
        for idx in idxs:
            print(f"Index: {idx[0]}")
            print(f"Definition: {idx[1]}\n")

if __name__ == "__main__":
    asyncio.run(check_duplicates_and_constraints())
