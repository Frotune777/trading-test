import asyncio
from sqlalchemy import text, inspect
from app.core.database import SessionLocal, engine

async def verify_hardening():
    async with SessionLocal() as db:
        print("--- Verifying Database Hardening ---")
        
        # 1. Check Table Renaming
        print("\nChecking Tables...")
        tables_res = await db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
        tables = [row[0] for row in tables_res.fetchall()]
        
        if "price_history" in tables:
            print("❌ 'price_history' STILL EXISTS!")
        else:
            print("✅ 'price_history' is GONE.")
            
        if "price_history_legacy" in tables:
            print("✅ 'price_history_legacy' EXISTS.")
        else:
            print("❌ 'price_history_legacy' MISSING.")
            
        # 2. Check Index
        print("\nChecking Indices on historical_ohlc...")
        idx_res = await db.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename='historical_ohlc'"))
        indices = idx_res.fetchall()
        
        found = False
        for idx in indices:
            if idx[0] == 'uix_ohlc_daily_date':
                print(f"✅ Found Index: {idx[0]}")
                print(f"   Definition: {idx[1]}")
                found = True
        
        if not found:
            print("❌ Index 'uix_ohlc_daily_date' NOT FOUND!")

if __name__ == "__main__":
    asyncio.run(verify_hardening())
