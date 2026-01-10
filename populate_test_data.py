#!/usr/bin/env python3
"""
Quick script to populate historical OHLC data for test symbols
"""
import asyncio
import yfinance as yf
from datetime import datetime, timezone
from sqlalchemy import select
import sys
import os

# Add backend to path
sys.path.insert(0, '/home/fortune/Desktop/Python_Projects/quad_trading/trading-test/backend')

from app.core.database import SessionLocal
from app.database.models_historical import HistoricalOHLC

async def populate_data(symbol: str, days: int = 30):
    """Fetch and populate historical data for a symbol"""
    print(f"\n📊 Fetching {days} days of data for {symbol}...")
    
    try:
        # Fetch from Yahoo Finance
        ticker = yf.Ticker(f"{symbol}.NS")
        df = ticker.history(period=f"{days}d", interval="1d")
        
        if df.empty:
            print(f"❌ No data returned for {symbol}")
            return False
            
        print(f"✓ Fetched {len(df)} candles")
        
        # Save to database
        async with SessionLocal() as db:
            inserted = 0
            skipped = 0
            
            for idx, row in df.iterrows():
                # Check if record already exists
                stmt = select(HistoricalOHLC).where(
                    HistoricalOHLC.symbol == symbol,
                    HistoricalOHLC.exchange == "NSE",
                    HistoricalOHLC.interval == "1d",
                    HistoricalOHLC.timestamp == idx.to_pydatetime().replace(tzinfo=timezone.utc)
                )
                existing = await db.execute(stmt)
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue
                
                # Insert new record
                ohlc = HistoricalOHLC(
                    symbol=symbol,
                    exchange="NSE",
                    interval="1d",
                    timestamp=idx.to_pydatetime().replace(tzinfo=timezone.utc),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                    source="yahoo_finance"
                )
                db.add(ohlc)
                inserted += 1
            
            await db.commit()
            print(f"✅ Inserted {inserted} new candles, skipped {skipped} existing")
            return True
            
    except Exception as e:
        print(f"❌ Error for {symbol}: {e}")
        return False

async def main():
    """Populate data for test symbols"""
    symbols = ["RELIANCE", "TCS", "INFY"]
    
    print("=" * 60)
    print("QUAD Historical Data Population")
    print("=" * 60)
    
    results = {}
    for symbol in symbols:
        results[symbol] = await populate_data(symbol, days=200)
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    for symbol, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{symbol}: {status}")
    
    print("\n✨ Data population complete!")

if __name__ == "__main__":
    asyncio.run(main())
