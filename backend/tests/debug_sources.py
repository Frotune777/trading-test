import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.data_sources.nse_master_data import NSEMasterData
from app.data_sources.nse_utils import NseUtils

def debug_sources():
    print("--- Debugging NSEMasterData ---")
    master = NSEMasterData()
    end = datetime.now()
    start = end - timedelta(days=5)
    
    try:
        df = master.get_history(symbol="RELIANCE", exchange="NSE", start=start, end=end, interval="1d")
        if df is not None:
            print(f"Columns: {df.columns.tolist()}")
            print(f"Index Name: {df.index.name}")
            print(f"df head:\n{df.head()}")
        else:
            print("NSEMasterData returned None")
    except Exception as e:
        print(f"NSEMasterData error: {e}")

    print("\n--- Debugging NseUtils.get_option_chain ---")
    nse = NseUtils()
    try:
        # NIFTY is an index
        df = nse.get_option_chain("NIFTY", indices=True)
        if df is not None:
            print(f"Option Chain columns: {df.columns.tolist()[:5]}...")
            print(f"Count: {len(df)}")
        else:
            print("NseUtils.get_option_chain returned None")
    except Exception as e:
        print(f"NseUtils error: {e}")

if __name__ == "__main__":
    debug_sources()
