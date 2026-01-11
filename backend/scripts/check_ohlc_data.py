import asyncio
import asyncpg

async def check_data():
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,
        user='postgres',
        password='postgres',
        database='quad_trading'
    )
    
    try:
        # Check if table exists
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'historical_ohlc'
            )
        """)
        
        if not exists:
            print("❌ historical_ohlc table does not exist")
            return
        
        # Count records
        count = await conn.fetchval('SELECT COUNT(*) FROM historical_ohlc')
        print(f"Total OHLC records: {count}")
        
        # Count by symbol
        rows = await conn.fetch("""
            SELECT symbol, COUNT(*) as count 
            FROM historical_ohlc 
            GROUP BY symbol 
            ORDER BY symbol
        """)
        
        if rows:
            print("\nRecords by symbol:")
            for row in rows:
                print(f"  {row['symbol']}: {row['count']} records")
        else:
            print("\n⚠️  No data found in historical_ohlc table")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_data())
