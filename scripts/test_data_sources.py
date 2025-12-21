#!/usr/bin/env python3
"""
Test all data sources for INFY (Infosys)
Check which sources are returning data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.data_sources.nse_complete import NSEComplete
from backend.app.data_sources.screener_enhanced import ScreenerEnhanced
import pandas as pd

def test_yahoo_finance(symbol):
    """Test Yahoo Finance data for symbol"""
    print(f"\n{'='*60}")
    print(f"🌍 TESTING YAHOO FINANCE FOR {symbol}")
    print(f"{'='*60}")
    
    try:
        nse = NSEComplete()
        
        # Test price data
        print("\n📊 Price Data:")
        price_data = nse.get_price_data(symbol)
        if price_data:
            print(f"✅ Got {len(price_data)} fields")
            for key, value in list(price_data.items())[:10]:
                print(f"   {key}: {value}")
            if len(price_data) > 10:
                print(f"   ... and {len(price_data) - 10} more fields")
        else:
            print("❌ No price data")
        
        # Test historical data
        print("\n📈 Historical Data (1 month):")
        hist_data = nse.get_historical_prices(symbol, period='1m', interval='1d', source='yahoo')
        if not hist_data.empty:
            print(f"✅ Got {len(hist_data)} records")
            print(f"   Columns: {list(hist_data.columns)}")
            print(f"   Date range: {hist_data['date'].min()} to {hist_data['date'].max()}")
            print(f"\n   Latest data:")
            print(hist_data.tail(3).to_string())
        else:
            print("❌ No historical data")
            
        return True
    except Exception as e:
        print(f"❌ Yahoo Finance failed: {e}")
        return False

def test_nse_direct(symbol):
    """Test NSE direct data for symbol"""
    print(f"\n{'='*60}")
    print(f"🇮🇳 TESTING NSE DIRECT FOR {symbol}")
    print(f"{'='*60}")
    
    try:
        nse = NSEComplete()
        
        # Test NSE historical (currently placeholder)
        print("\n📈 NSE Historical Data:")
        hist_data = nse._get_nse_historical(symbol, period='1m', interval='1d')
        if not hist_data.empty:
            print(f"✅ Got {len(hist_data)} records")
            print(hist_data.head())
        else:
            print("⚠️  NSE historical not yet implemented (returns empty)")
            print("   (This will trigger Yahoo fallback in auto mode)")
            
        return False  # Currently not implemented
    except Exception as e:
        print(f"❌ NSE Direct failed: {e}")
        return False

def test_screener(symbol):
    """Test Screener.in data for symbol"""
    print(f"\n{'='*60}")
    print(f"📊 TESTING SCREENER.IN FOR {symbol}")
    print(f"{'='*60}")
    
    try:
        screener = ScreenerEnhanced()
        
        # Test complete data
        print("\n📋 Complete Data:")
        complete_data = screener.get_complete_data(symbol)
        
        if complete_data:
            print(f"✅ Got data for {len(complete_data)} categories:")
            
            for category, data in complete_data.items():
                print(f"\n   📁 {category}:")
                if isinstance(data, dict):
                    if data:
                        print(f"      ✅ {len(data)} fields")
                        for k, v in list(data.items())[:3]:
                            print(f"         {k}: {v}")
                    else:
                        print(f"      ⚠️  Empty dict")
                elif isinstance(data, pd.DataFrame):
                    if not data.empty:
                        print(f"      ✅ DataFrame with {len(data)} rows, {len(data.columns)} columns")
                        print(f"         Columns: {list(data.columns)[:5]}")
                    else:
                        print(f"      ⚠️  Empty DataFrame")
                else:
                    print(f"      ❓ Type: {type(data)}")
        else:
            print("❌ No data from Screener")
            
        return bool(complete_data)
    except Exception as e:
        print(f"❌ Screener failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    symbol = "INFY"
    
    print(f"\n{'#'*60}")
    print(f"# DATA SOURCE TEST FOR {symbol} (INFOSYS)")
    print(f"{'#'*60}")
    
    # Test all sources
    results = {
        'Yahoo Finance': test_yahoo_finance(symbol),
        'NSE Direct': test_nse_direct(symbol),
        'Screener.in': test_screener(symbol)
    }
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    for source, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {source}: {'Working' if status else 'Not Working / Not Implemented'}")
    
    working_sources = [s for s, status in results.items() if status]
    print(f"\n🎯 {len(working_sources)}/{len(results)} sources providing data")
    
    if working_sources:
        print(f"✅ Recommended: Use {working_sources[0]}")

if __name__ == "__main__":
    main()
