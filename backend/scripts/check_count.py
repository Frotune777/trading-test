import asyncio
import asyncpg

async def count_records():
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,
        user='postgres',
        password='postgres',
        database='quad_trading'
    )
    
    count = await conn.fetchval("SELECT count(*) FROM historical_ohlc")
    print(f"Total records in historical_ohlc: {count}")
    
    # Check breakdown by source
    rows = await conn.fetch("SELECT source, count(*) FROM historical_ohlc GROUP BY source")
    for row in rows:
        print(f"Source {row['source']}: {row['count']}")

    await conn.close()

asyncio.run(count_records())
