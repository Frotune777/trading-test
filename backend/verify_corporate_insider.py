from datetime import datetime
from app.data_sources.nse_utils import NseUtils
import pandas as pd

nse = NseUtils()

print("\n--- Testing Corporate Actions ---")
try:
    df_corp = nse.get_corporate_action()
    if df_corp is not None and not df_corp.empty:
        print("Success! Corporate Actions found:")
        print(df_corp.head())
    else:
        print("Failed: Corporate Actions return None or empty")
except Exception as e:
    print(f"Exception in get_corporate_action: {e}")

print("\n--- Testing Insider Trading ---")
try:
    df_insider = nse.get_insider_trading()
    if df_insider is not None and not df_insider.empty:
        print("Success! Insider Trading data found:")
        print(df_insider.head())
    else:
        print("Failed: Insider Trading return None or empty")
except Exception as e:
    print(f"Exception in get_insider_trading: {e}")
