import asyncio
import asyncpg

async def check_constraints():
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,
        user='postgres',
        password='postgres',
        database='quad_trading'
    )
    
    rows = await conn.fetch("""
        SELECT
            tc.constraint_name, 
            tc.constraint_type, 
            kcu.column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
        WHERE tc.table_name = 'historical_ohlc'
        ORDER BY tc.constraint_name, kcu.ordinal_position;
    """)
    
    print("Constraints on historical_ohlc:")
    for row in rows:
        print(f"  {row['constraint_name']} ({row['constraint_type']}): {row['column_name']}")
        
    # Also check indices
    rows_idx = await conn.fetch("""
        SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'historical_ohlc';
    """)
    print("\nIndices on historical_ohlc:")
    for row in rows_idx:
        print(f"  {row['indexname']}: {row['indexdef']}")

    await conn.close()

asyncio.run(check_constraints())
