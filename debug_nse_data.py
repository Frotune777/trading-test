import sys
import os
from datetime import datetime
import pandas as pd

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.data_sources.nse_utils import NseUtils

def debug_data():
    nse = NseUtils()
    
    print("=== INSIDER TRADING ===")
    df = nse.get_insider_trading()
    if df is not None:
        print(f"Columns: {df.columns.tolist()}")
        if not df.empty:
            print(f"First row Dict: {df.iloc[0].to_dict()}")
            # Check for INDOSTAR
            if 'symbol' in df.columns:
                print(f"INDOSTAR rows: {len(df[df['symbol'] == 'INDOSTAR'])}")
            
    print("\n=== BULK DEALS ===")
    df = nse.get_bulk_deals()
    if df is not None:
        print(f"Columns: {df.columns.tolist()}")
        if not df.empty:
            print(df.head(2).to_string())

if __name__ == "__main__":
    debug_data()
