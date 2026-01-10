#!/usr/bin/env python3
"""
Populate historical data using the backend API
"""
import requests
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000/api/v1"

def populate_symbol(symbol: str, days: int = 200):
    """Trigger data ingestion via API"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    print(f"\n📊 Triggering ingestion for {symbol} ({start_date} to {end_date})...")
    
    url = f"{API_BASE}/data/ingest"
    params = {
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "source": "yahoo",
        "timeframe": "1d"
    }
    
    try:
        response = requests.post(url, params=params, timeout=30)
        result = response.json()
        
        if result.get("status") == "success":
            print(f"✅ {symbol}: Inserted {result.get('rows_inserted', 0)} candles")
            return True
        else:
            print(f"⚠️  {symbol}: {result.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ {symbol}: {e}")
        return False

def main():
    symbols = ["RELIANCE", "TCS", "INFY"]
    
    print("=" * 60)
    print("QUAD Historical Data Population (via API)")
    print("=" * 60)
    
    results = {}
    for symbol in symbols:
        results[symbol] = populate_symbol(symbol, days=200)
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    for symbol, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{symbol}: {status}")
    
    print("\n✨ Data population complete!")

if __name__ == "__main__":
    main()
