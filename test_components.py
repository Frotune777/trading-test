#!/usr/bin/env python3
"""
Test specific components in detail
Usage: python test_components.py [nse|yahoo|screener|database|all]
"""

import sys
import argparse
from pathlib import Path

def test_nse_detailed():
    """Detailed NSE testing"""
    print("\n" + "="*60)
    print("DETAILED NSE TEST")
    print("="*60 + "\n")
    
    from data_sources.nse_complete import NSEComplete
    
    nse = NSEComplete()
    test_symbol = "RELIANCE"
    
    tests = {
        "Company Info": lambda: nse.get_company_info(test_symbol),
        "Price Data": lambda: nse.get_price_data(test_symbol),
        "Historical Prices": lambda: nse.get_historical_prices(test_symbol, period='1m'),
        "Trading Holidays": lambda: nse.trading_holidays(list_only=True),
        "Gainers/Losers": lambda: nse.get_gainers_losers(),
        "FII/DII Activity": lambda: nse.fii_dii_activity(),
        "Equity List": lambda: nse.get_equity_full_list(list_only=True)[:5],
    }
    
    for test_name, test_func in tests.items():
        try:
            result = test_func()
            print(f"✓ {test_name}: {type(result).__name__}")
            if isinstance(result, dict):
                print(f"  Keys: {list(result.keys())[:5]}")
            elif isinstance(result, list):
                print(f"  Items: {len(result)}")
        except Exception as e:
            print(f"✗ {test_name}: {str(e)[:100]}")

def test_yahoo_detailed():
    """Detailed Yahoo Finance testing"""
    print("\n" + "="*60)
    print("DETAILED YAHOO FINANCE TEST")
    print("="*60 + "\n")
    
    from data_sources.yahoo_finance import YahooFinance
    
    yahoo = YahooFinance()
    symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
    
    for symbol in symbols:
        try:
            print(f"\n{symbol}:")
            
            price_data = yahoo.get_price_data(symbol)
            print(f"  Price: ₹{price_data.get('current_price', 'N/A')}")
            
            hist_data = yahoo.get_historical_prices(symbol, period='5d')
            if hist_data is not None:
                print(f"  Historical: {len(hist_data)} rows")
            
        except Exception as e:
            print(f"  Error: {str(e)[:100]}")

def test_database_detailed():
    """Detailed database testing"""
    print("\n" + "="*60)
    print("DETAILED DATABASE TEST")
    print("="*60 + "\n")
    
    from database.db_manager import DatabaseManager
    import pandas as pd
    from datetime import datetime, timedelta
    
    db = DatabaseManager(db_path='test_detailed.db')
    
    # Add test data
    print("1. Adding test company...")
    db.add_company(
        symbol="TESTSTOCK",
        company_name="Test Stock Ltd.",
        sector="Technology",
        industry="Software"
    )
    
    print("2. Adding snapshot...")
    db.update_snapshot("TESTSTOCK", {
        'current_price': 1234.56,
        'market_cap': 50000.0,
        'pe_ratio': 25.5,
        'roe': 18.5
    })
    
    print("3. Adding price history...")
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    price_df = pd.DataFrame({
        'date': dates,
        'open': [1200 + i for i in range(30)],
        'high': [1220 + i for i in range(30)],
        'low': [1190 + i for i in range(30)],
        'close': [1210 + i for i in range(30)],
        'volume': [1000000 + i*10000 for i in range(30)]
    })
    db.save_price_history("TESTSTOCK", price_df)
    
    print("4. Reading back data...")
    company = db.get_company("TESTSTOCK")
    print(f"   Company: {company.get('company_name')}")
    
    snapshot = db.get_snapshot("TESTSTOCK")
    print(f"   Price: ₹{snapshot.get('current_price')}")
    
    history = db.get_price_history("TESTSTOCK", days=30)
    print(f"   History: {len(history)} rows")
    
    print("5. Database stats:")
    stats = db.get_database_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    db.close()
    
    # Cleanup
    Path('test_detailed.db').unlink()
    print("\n✓ All database operations successful")

def test_aggregator_detailed():
    """Detailed aggregator testing"""
    print("\n" + "="*60)
    print("DETAILED AGGREGATOR TEST")
    print("="*60 + "\n")
    
    from core.hybrid_aggregator import HybridAggregator
    
    aggregator = HybridAggregator(use_cache=False)
    
    print("Testing with RELIANCE...")
    
    print("\n1. Quick Quote (NSE + Yahoo):")
    quote = aggregator.get_quick_quote("RELIANCE")
    if quote:
        print(f"   Price: ₹{quote.get('current_price', 'N/A')}")
        print(f"   Change: {quote.get('change_percent', 'N/A')}%")
        print(f"   Sources: {quote.get('_metadata', {}).get('sources_used', [])}")
    
    print("\n2. Stock Data (with history):")
    stock_data = aggregator.get_stock_data("RELIANCE", include_historical=True)
    if stock_data:
        print(f"   Company: {stock_data.get('company_info', {}).get('name', 'N/A')}")
        if 'historical_prices' in stock_data and stock_data['historical_prices'] is not None:
            print(f"   Historical: {len(stock_data['historical_prices'])} rows")

def main():
    parser = argparse.ArgumentParser(description='Test Fortune Trading components')
    parser.add_argument(
        'component',
        nargs='?',
        default='all',
        choices=['nse', 'yahoo', 'screener', 'database', 'aggregator', 'all'],
        help='Component to test'
    )
    
    args = parser.parse_args()
    
    tests = {
        'nse': test_nse_detailed,
        'yahoo': test_yahoo_detailed,
        'database': test_database_detailed,
        'aggregator': test_aggregator_detailed,
    }
    
    if args.component == 'all':
        for test_func in tests.values():
            try:
                test_func()
            except Exception as e:
                print(f"\n❌ Test failed: {e}")
                import traceback
                traceback.print_exc()
    else:
        tests[args.component]()

if __name__ == "__main__":
    main()