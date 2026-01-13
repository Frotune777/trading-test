import sys
import os

# Add the current directory to sys.path so 'app' can be imported
sys.path.append(os.getcwd())

try:
    from app.data_sources.nse_utils import NseUtils
except ImportError as e:
    print(f"Import Error: {e}")
    # Try adding parent dir if run from app/
    sys.path.append(os.path.join(os.getcwd(), '..'))
    from app.data_sources.nse_utils import NseUtils

print("Initializing NseUtils...")
try:
    nse = NseUtils()
except Exception as e:
    print(f"Init Failed: {e}")
    sys.exit(1)

print("\n--- Testing Equity Info (TCS) ---")
try:
    data = nse.equity_info("TCS")
    if data:
        print(f"Top Level Keys: {list(data.keys())}")
        if 'metaData' in data:
            print(f"metaData keys: {list(data['metaData'].keys())}")
            print(f"metaData sample: {str(data['metaData'])[:300]}")
        if 'tradeInfo' in data:
            print(f"tradeInfo keys: {list(data['tradeInfo'].keys())}")
            print(f"tradeInfo sample: {str(data['tradeInfo'])[:300]}")

        
    if data and 'priceInfo' in data:

        if 'metadata' in data:
            print(f"Timestamp: {data['metadata'].get('lastUpdateTime')}")
        elif 'metaData' in data:
             print(f"Timestamp: {data['metaData'].get('lastUpdateTime') or data.get('timestamp')}")

    else:

        print(f"Failed: Data is {type(data)}")
        if data: print(data.keys())
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n--- Testing Option Chain (TCS) ---")
try:
    df = nse.get_option_chain("TCS")
    if not df.empty:
        print(f"Success! Rows: {len(df)}")
        print(df.head(2))
    else:
        print("Failed: Empty DataFrame")
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
