# debug_master.py
import sys
from pathlib import Path
import pandas as pd

# Ensure external_libs is in the path
sys.path.insert(0, str(Path(__file__).parent / "external_libs"))

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

print("--- STARTING FINAL DEBUG SCRIPT ---")

try:
    from nse_master_data import NSEMasterData
    print("✅ Successfully imported NSEMasterData.")
except ImportError as e:
    print(f"❌ FAILED to import NSEMasterData: {e}")
    sys.exit()

# 1. Initialize
print("\n[STEP 1] Initializing NSEMasterData...")
master = NSEMasterData()
print("✅ Initialization successful.")

# 2. Download
print("\n[STEP 2] Calling download_symbol_master()...")
master.download_symbol_master()
print("✅ download_symbol_master() executed.")

# 3. Inspect internal data
print("\n[STEP 3] Inspecting internal master.nse_data...")
if master.nse_data is not None and not master.nse_data.empty:
    print(f"✅ master.nse_data is POPULATED with {len(master.nse_data)} rows.")
    print("--- DataFrame Columns: ---")
    print(master.nse_data.columns.tolist())
    print("\n--- First 5 rows of master.nse_data: ---")
    print(master.nse_data.head())
    print("-" * 40)
else:
    print("❌ FATAL: master.nse_data is EMPTY or None. The download is failing.")
    sys.exit()

# 4. DIRECTLY TEST THE SEARCH METHOD
print("\n[STEP 4] Testing master.search('TCS', exchange='NSE', match=True)...")
try:
    # This is the exact call that happens during validation
    tcs_exact_search = master.search('TCS', exchange='NSE', match=True)
    
    if not tcs_exact_search.empty:
        print("✅ SUCCESS: master.search() for 'TCS' found a result!")
        print(tcs_exact_search)
    else:
        print("❌ FAILURE: master.search() for 'TCS' returned an empty DataFrame.")
        print("   This is the root cause of the validation error.")
        
        print("\n   Let's check if 'TCS' exists in the 'TradingSymbol' column at all...")
        # Manually search the DataFrame to bypass the search method
        manual_find = master.nse_data[master.nse_data['TradingSymbol'].str.upper() == 'TCS']
        if not manual_find.empty:
            print("   INTERESTING: Manually found 'TCS' in the DataFrame. This means the LOGIC inside the search() method is flawed.")
            print(manual_find)
        else:
            print("   CONFIRMED: 'TCS' does not exist in the 'TradingSymbol' column of the downloaded data.")

except Exception as e:
    print(f"❌ An exception occurred during search: {e}")

print("\n--- DEBUG SCRIPT FINISHED ---")
