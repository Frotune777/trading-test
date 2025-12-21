"""
Basic usage examples
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.hybrid_aggregator import HybridAggregator
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


def example_single_stock():
    """Fetch data for a single stock."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Single Stock Data")
    print("="*70)
    
    aggregator = HybridAggregator()
    
    # Get complete data for TCS
    tcs = aggregator.get_stock_data('TCS')
    
    print(f"\n🏢 Company: {tcs['company_info'].get('company_name')}")
    print(f"💰 Price: ₹{tcs['price'].get('last_price')}")
    print(f"📈 Change: {tcs['price'].get('change_percent')}%")
    print(f"📊 P/E Ratio: {tcs['price'].get('pe_ratio')}")
    print(f"📡 Sources used: {', '.join(tcs['sources']['used'])}")
    
    if tcs.get('historical_prices') is not None:
        print(f"\n📊 Historical data points: {len(tcs['historical_prices'])}")
        print("\nLast 5 days:")
        print(tcs['historical_prices'].tail())


def example_quick_quotes():
    """Get quick quotes for multiple stocks."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Quick Quotes")
    print("="*70)
    
    aggregator = HybridAggregator()
    
    symbols = ['TCS', 'INFY', 'WIPRO', 'HCLTECH']
    
    print("\n💹 Live Quotes:\n")
    for symbol in symbols:
        quote = aggregator.get_quick_quote(symbol)
        if 'last_price' in quote:
            change = quote.get('change_percent', 0)
            arrow = "↗️" if change > 0 else "↘️" if change < 0 else "→"
            print(f"{symbol:10s} ₹{quote['last_price']:8.2f} {arrow} {change:+6.2f}%")


def example_batch_fetch():
    """Batch fetch multiple stocks."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Batch Fetch")
    print("="*70)
    
    aggregator = HybridAggregator()
    
    symbols = ['TCS', 'INFY', 'WIPRO']
    
    print(f"\n📦 Fetching {len(symbols)} stocks in parallel...\n")
    
    results = aggregator.batch_fetch(symbols, max_workers=3)
    
    print("\n📊 Results:\n")
    for symbol, data in results.items():
        if 'error' not in data:
            price = data['price'].get('last_price', 'N/A')
            print(f"✅ {symbol}: ₹{price}")
        else:
            print(f"❌ {symbol}: {data['error']}")


def example_cache_performance():
    """Demonstrate caching performance."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Cache Performance")
    print("="*70)
    
    import time
    
    aggregator = HybridAggregator()
    
    symbol = 'TCS'
    
    # First call (no cache)
    print(f"\n⏱️  First call (fetching from sources)...")
    start = time.time()
    data1 = aggregator.get_stock_data(symbol)
    time1 = time.time() - start
    print(f"   Time: {time1:.2f}s")
    
    # Second call (from cache)
    print(f"\n⚡ Second call (from cache)...")
    start = time.time()
    data2 = aggregator.get_stock_data(symbol)
    time2 = time.time() - start
    print(f"   Time: {time2:.2f}s")
    
    print(f"\n🚀 Speedup: {time1/time2:.1f}x faster!")
    
    # Show cache stats
    stats = aggregator.cache.get_stats()
    print(f"\n📊 Cache Stats:")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit Rate: {stats['hit_rate']}")


if __name__ == '__main__':
    example_single_stock()
    example_quick_quotes()
    example_batch_fetch()
    example_cache_performance()