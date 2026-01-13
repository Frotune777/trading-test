import asyncio
import asyncpg

async def add_column():
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,
        user='postgres',
        password='postgres',
        database='quad_trading'
    )
    
    try:
        await conn.execute("ALTER TABLE historical_ohlc ADD COLUMN IF NOT EXISTS delivery_quantity BIGINT")
        print("✅ Added delivery_quantity column")
        
        await conn.execute("ALTER TABLE historical_ohlc ADD COLUMN IF NOT EXISTS delivery_percentage DECIMAL(5,2)")
        print("✅ Added delivery_percentage column")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

asyncio.run(add_column())
