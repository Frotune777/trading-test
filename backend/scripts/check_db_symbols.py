import asyncio
import asyncpg

async def check_symbols():
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,
        user='postgres',
        password='postgres',
        database='quad_trading'
    )
    
    rows = await conn.fetch("SELECT symbol FROM companies ORDER BY symbol LIMIT 10")
    print("Sample symbols in DB:")
    for row in rows:
        print(f"  {row['symbol']}")

    await conn.close()

asyncio.run(check_symbols())
