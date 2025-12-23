
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.reasoning.snapshot_builder import SnapshotBuilder
import logging

# Configure logging to see info
logging.basicConfig(level=logging.INFO)

def verify_metrics():
    print("Initializing SnapshotBuilder...")
    builder = SnapshotBuilder()
    
    symbol = "RELIANCE"
    print(f"Building snapshot for {symbol}...")
    
    try:
        snapshot = builder.build_snapshot(symbol)
        
        print("\n--- LIQUIDITY METRICS ---")
        print(f"Bid Price: {snapshot.bid_price}")
        print(f"Ask Price: {snapshot.ask_price}")
        print(f"Bid Qty: {snapshot.bid_qty}")
        print(f"Ask Qty: {snapshot.ask_qty}")
        print(f"Spread %: {snapshot.spread_pct}")
        
        print("\n--- SENTIMENT METRICS ---")
        print(f"OI Change: {snapshot.oi_change}")
        
        # Validation
        if snapshot.bid_qty is not None and snapshot.ask_qty is not None:
            print("\n✅ Liquidity metrics present")
        else:
            print("\n❌ Liquidity metrics MISSING")
            
        if snapshot.oi_change is not None:
            print("✅ Sentiment metrics present")
        else:
            print("❌ Sentiment metrics MISSING")
        
        # DEBUG: Check raw data
        print("\n--- DEBUG INFO ---")
        try:
            print("Fetching raw equity info...")
            quote = builder.nse_derivatives.nse_utils.equity_info(symbol)
            print(f"Equity Info Keys: {quote.keys() if quote else 'None'}")
            if quote and 'tradeData' in quote:
                 print(f"OrderBook keys: {quote['tradeData'].get('marketDeptOrderBook', {}).keys()}")
            
            print("Fetching raw option chain...")
            oc = builder.nse_derivatives.get_option_chain(symbol)
            print(f"Option Chain Empty? {oc.empty}")
            if not oc.empty:
                print(f"Columns: {oc.columns}")
                print(f"Head: {oc.head(1)}")
        except Exception as e:
            print(f"Debug Error: {e}")
            
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_metrics()
