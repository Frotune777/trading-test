import sys
import os
import pandas as pd

# Add parent dir to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.app.data_sources.nse_utils import NseUtils

def check_structure():
    print("Fetching corporate actions...")
    nse = NseUtils()
    # Fetch for last 30 days
    df = nse.get_corporate_action()
    
    if df is not None and not df.empty:
        print("Columns:", df.columns.tolist())
        print("First row:", df.iloc[0].to_dict())
    else:
        print("No data received or empty dataframe.")

if __name__ == "__main__":
    check_structure()
