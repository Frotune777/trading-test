import nselib
from nselib import capital_market
from nselib import derivatives

print("🚀 Testing nselib capabilities...")

try:
    print("\n📊 Testing Derivatives (Option Chain)...")
    # Fetch option chain for NIFTY
    oc = derivatives.nse_live_option_chain("NIFTY")
    if not oc.empty:
        print(f"✅ Option Chain Fetched: {len(oc)} rows")
        print(oc.head(3))
    else:
        print("❌ Option Chain Empty")
except Exception as e:
    print(f"💥 Derivatives Error: {e}")

try:
    print("\n🏢 Testing Institutional Activity (FII/DII)...")
    # Note: nselib naming might be different, checking standard functions
    # Based on library docs (or common knowledge of it)
    try:
        fii_stats = capital_market.fii_dii_trading_activity()
        if not fii_stats.empty:
            print(f"✅ FII/DII Stats Fetched: {len(fii_stats)} rows")
            print(fii_stats)
        else:
            print("❌ FII/DII Stats Empty")
    except AttributeError:
        print("⚠️ fii_dii_trading_activity method not found, checking alternatives...")

except Exception as e:
    print(f"💥 Institutional Error: {e}")

try:
    print("\n📈 Testing Market Breadth (Bhav Copy)...")
    bhav = capital_market.bhav_copy_equities("20-12-2024") # Use a recent valid trading date
    if not bhav.empty:
        print(f"✅ Bhav Copy Fetched: {len(bhav)} rows")
    else:
        print("❌ Bhav Copy Empty")
except Exception as e:
    print(f"💥 Market Breadth Error: {e}")
