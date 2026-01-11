import asyncio
import asyncpg

async def check_timestamps():
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,
        user='postgres',
        password='postgres',
        database='quad_trading'
    )
    
    row = await conn.fetchrow("""
        SELECT timestamp FROM historical_ohlc 
        WHERE symbol='WIPRO' 
        ORDER BY timestamp DESC LIMIT 1
    """)
    print(f"Latest WIPRO timestamp: {row['timestamp']}")
    print(f"Type: {type(row['timestamp'])}")
    
    await conn.close()

asyncio.run(check_timestamps())
