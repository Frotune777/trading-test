"""
Simple script to create companies table using raw SQL via Docker PostgreSQL
"""
import asyncio
import asyncpg

async def create_and_populate():
    """Create companies table and add sample data"""
    
    # Connect to Docker PostgreSQL database
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,  # Docker mapped port
        user='postgres',
        password='postgres',
        database='quad_trading'
    )
    
    try:
        # Read SQL file
        with open('/home/fortune/Desktop/Python_Projects/quad_trading/trading-test/backend/scripts/create_companies.sql', 'r') as f:
            sql = f.read()
        
        # Execute SQL
        await conn.execute(sql)
        
        print("✅ Companies table created successfully")
        
        # Verify data
        rows = await conn.fetch("SELECT symbol, name, sector FROM companies ORDER BY sector, symbol")
        
        print(f"\n✅ Inserted {len(rows)} companies:")
        print("\nEnergy Sector:")
        for row in rows:
            if row['sector'] == 'Energy':
                print(f"  - {row['symbol']}: {row['name']}")
        
        print("\nInformation Technology Sector:")
        for row in rows:
            if row['sector'] == 'Information Technology':
                print(f"  - {row['symbol']}: {row['name']}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_and_populate())
