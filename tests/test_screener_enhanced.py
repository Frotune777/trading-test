"""
Test enhanced Screener scraper - DEBUG VERSION
"""

from data_sources.screener_enhanced import ScreenerEnhanced
import pandas as pd
import logging

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(levelname)s: %(message)s'
)

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_rows', None)

# Initialize
screener = ScreenerEnhanced()

# Get complete data
print("="*80)
print("📊 TESTING ENHANCED SCREENER.IN DATA - DEBUG MODE")
print("="*80)

symbol = 'TCS'
data = screener.get_complete_data(symbol)

# 1. Company Info
print("\n1️⃣  Company Information:")
if data.get('company_info'):
    for key, value in data['company_info'].items():
        print(f"   {key}: {value}")
else:
    print("   ❌ No company info found")

# 2. Key Metrics
print("\n2️⃣  Key Metrics:")
if data.get('key_metrics'):
    for key, value in data['key_metrics'].items():
        print(f"   {key}: {value}")
else:
    print("   ❌ No key metrics found")

# 3. Quarterly Results
print("\n3️⃣  Quarterly Results:")
if data.get('quarterly_results') is not None:
    df = data['quarterly_results']
    print(f"   ✅ Shape: {df.shape}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   First 3 rows:\n{df.head(3)}")
else:
    print("   ❌ No quarterly results found")

# 4. Profit & Loss
print("\n4️⃣  Profit & Loss:")
if data.get('profit_loss') is not None:
    df = data['profit_loss']
    print(f"   ✅ Shape: {df.shape}")
    print(f"   Available years: {len(df.columns)}")
else:
    print("   ❌ No P&L data found")

# 5. Balance Sheet
print("\n5️⃣  Balance Sheet:")
if data.get('balance_sheet') is not None:
    df = data['balance_sheet']
    print(f"   ✅ Shape: {df.shape}")
else:
    print("   ❌ No balance sheet found")

# 6. Cash Flow
print("\n6️⃣  Cash Flow:")
if data.get('cash_flow') is not None:
    df = data['cash_flow']
    print(f"   ✅ Shape: {df.shape}")
else:
    print("   ❌ No cash flow found")

# 7. Ratios
print("\n7️⃣  Detailed Ratios:")
if data.get('ratios') is not None:
    df = data['ratios']
    print(f"   ✅ Shape: {df.shape}")
else:
    print("   ❌ No ratios found")

# 8. Shareholding
print("\n8️⃣  Shareholding Pattern:")
if data.get('shareholding') is not None:
    df = data['shareholding']
    print(f"   ✅ Shape: {df.shape}")
else:
    print("   ❌ No shareholding data found")

# 9. Peers (DEBUGGING)
print("\n9️⃣  Peer Comparison:")
if data.get('peer_comparison') is not None:
    df = data['peer_comparison']
    print(f"   ✅ Shape: {df.shape}")
    print(f"\n   Peer companies:")
    print(df.to_string())
else:
    print("   ❌ No peer data found")
    print("   📁 Check these debug files for analysis:")
    print("      - tcs_full_page.html")
    print("      - peers_section.html")

print("\n" + "="*80)
print("✅ TEST COMPLETE - Check debug files!")
print("="*80)