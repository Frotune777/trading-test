import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_schema():
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5438/quad_trading"
    print(f"Connecting to {DATABASE_URL}...")
    
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.connect() as conn:
        tables_to_check = ['quad_decisions', 'decision_ledger']

        for table_name in tables_to_check:
            print(f"\n--- Checking schema for table: {table_name} ---")
            rows = await conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'"))
            
            rows_list = rows.fetchall()
            if not rows_list:
                print(f"No columns found for table '{table_name}'. It might not exist or be empty.")
            else:
                print(f"Columns in {table_name}:")
                for row in rows_list:
                    print(f"- {row[0]}: {row[1]}")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_schema())

