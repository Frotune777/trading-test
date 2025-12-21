import nselib
from nselib import capital_market
from nselib import derivatives
import yfinance as yf
import pandas as pd

print("🚀 Testing Data Sources...")

# 1. Derivatives (Option Chain)
print("\n[1] Testing Option Chain...")
try:
    print("  👉 Trying nselib...")
    oc = derivatives.nse_live_option_chain("NIFTY")
    print(f"  ✅ nselib: {len(oc)} rows")
except Exception as e:
    print(f"  ❌ nselib failed: {e}")

try:
    print("  👉 Trying yfinance...")
    # Nifty symbol in yahoo is ^NSEI
    nifty = yf.Ticker("^NSEI")
    opts = nifty.option_chain()
    print(f"  ✅ yfinance: {len(opts.calls)} calls, {len(opts.puts)} puts")
except Exception as e:
    print(f"  ❌ yfinance failed: {e}")

# 2. Institutional Activity
print("\n[2] Testing FII/DII...")
try:
    # Try generic delivery data or similar from nselib if direct FII method missing
    # But for now, just checking if we can scrape it or if nselib has a different method
    # Skipping direct nselib call as it failed before
    pass
except Exception as e:
    print(f"  ❌ nselib failed: {e}")
    
# 3. Market Breadth
print("\n[3] Testing Market Breadth...")
try:
    # Try fetching Nifty 50 constituents to check breadth
    nifty50 = capital_market.nifty50_equity_list()
    if not nifty50.empty:
        print(f"  ✅ nselib Nifty50: {len(nifty50)} rows")
    else:
        print("  ❌ nselib Nifty50 empty")
except Exception as e:
    print(f"  ❌ nselib failed: {e}")
