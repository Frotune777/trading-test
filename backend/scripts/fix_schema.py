
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def fix_schema():
    # Hardcoded for local fix execution via host port 5438
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5438/quad_trading"
    print(f"Connecting to {DATABASE_URL}...")
    
    engine = create_async_engine(DATABASE_URL)
    
    print("Fixing database schema...")
    async with engine.begin() as conn:
        # 1. Fix quad_decisions
        print("Checking quad_decisions...")
        try:
            await conn.execute(text("ALTER TABLE quad_decisions ADD COLUMN IF NOT EXISTS pillar_explanations JSON"))
            print("Added pillar_explanations to quad_decisions")
        except Exception as e:
            print(f"Error updating quad_decisions: {e}")

        # 2. Fix decision_ledger
        print("Checking decision_ledger...")
        try:
            await conn.execute(text("ALTER TABLE decision_ledger ADD COLUMN IF NOT EXISTS validity_window_mins INTEGER DEFAULT 15"))
            print("Added validity_window_mins to decision_ledger")
        except Exception as e:
            print(f"Error adding validity_window_mins: {e}")
            
        try:
            await conn.execute(text("ALTER TABLE decision_ledger ADD COLUMN IF NOT EXISTS strategy_name_snapshot VARCHAR(100)"))
            print("Added strategy_name_snapshot to decision_ledger")
        except Exception as e:
            print(f"Error adding strategy_name_snapshot: {e}")
            
    await engine.dispose()
    print("Schema fix complete.")

if __name__ == "__main__":
    asyncio.run(fix_schema())
