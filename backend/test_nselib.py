try:
    from nselib import capital_market, derivatives
    print("nselib imported successfully")
except ImportError:
    print("nselib not found")
    exit(1)

import pandas as pd

print("\n--- Testing nselib Option Chain ---")
try:
    # nselib documentation suggests derivatives.nse_live_option_chain
    # But checking source or common usage
    try:
        df = derivatives.nse_live_option_chain("TCS")
        print(f"Status: Success? {not df.empty}")
        if not df.empty:
            print(df.head())
        else:
            print("Empty DataFrame")
    except Exception as e:
        print(f"Failed call: {e}")

except Exception as e:
    print(f"General Error: {e}")
