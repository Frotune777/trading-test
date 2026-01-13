import asyncio
from sqlalchemy import text
from app.core.database import SessionLocal

async def fix_duplicates():
    async with SessionLocal() as db:
        print("--- Starting Deduplication Process ---")
        
        # 1. Identify groups of (symbol, interval, date) having multiple entries
        # We assume 1d interval for now as that's where the issue was seen
        find_dups_query = text("""
            SELECT symbol, date(timestamp) as day_date, count(*)
            FROM historical_ohlc
            WHERE interval = '1d'
            AND exchange = 'NSE'
            GROUP BY symbol, day_date
            HAVING count(*) > 1
        """)
        
        result = await db.execute(find_dups_query)
        dup_groups = result.fetchall()
        
        print(f"Found {len(dup_groups)} groups with duplicates (Same Day, Multiple Timestamps)")
        
        deleted_count = 0
        
        for group in dup_groups:
            symbol = group[0]
            day_date = group[1]
            
            # Fetch all records for this group
            records_query = text("""
                SELECT id, timestamp
                FROM historical_ohlc
                WHERE symbol = :symbol
                AND interval = '1d'
                AND exchange = 'NSE'
                AND date(timestamp) = :day_date
                ORDER BY timestamp
            """)
            
            recs = await db.execute(records_query, {"symbol": symbol, "day_date": day_date})
            all_recs = recs.fetchall()
            
            # Strategy:
            # 1. Prefer 00:00:00
            # 2. If multiple 00:00:00 (unlikely with unique constraint on full TS), take latest ID?
            # 3. If no 00:00:00, take the one closest to 00:00:00? Or just the first one?
            
            keep_id = None
            
            # Check for exact 00:00:00
            perfect_matches = [r for r in all_recs if r.timestamp.hour == 0 and r.timestamp.minute == 0 and r.timestamp.second == 0]
            
            if perfect_matches:
                keep_id = perfect_matches[0].id # Keep the first perfect match
            else:
                # No 00:00:00, keep the one with the LATEST timestamp (assuming it's the final close?)
                # Or earliest? 
                # In our case 18:30 prev day vs 00:00 current day provided 00:00.
                # If we only have 15:59 and 18:30... 15:59 is closer to close.
                # Let's keep the last one in the list (ordered by timestamp)
                keep_id = all_recs[-1].id
            
            # Delete others
            for r in all_recs:
                if r.id != keep_id:
                    print(f"Deleting duplicate ID {r.id} for {symbol} on {day_date} (TS: {r.timestamp})")
                    await db.execute(text("DELETE FROM historical_ohlc WHERE id = :id"), {"id": r.id})
                    deleted_count += 1
        
        await db.commit()
        print(f"\nCompleted. Deleted {deleted_count} duplicate records.")

if __name__ == "__main__":
    asyncio.run(fix_duplicates())
