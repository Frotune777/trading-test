import yfinance as yf
import pandas as pd
import requests

print("🚀 Refining Tests...")

# 1. Option Chain for Stock
print("\n[1] Testing Option Chain (RELIANCE.NS)...")
try:
    stock = yf.Ticker("RELIANCE.NS")
    opts = stock.option_chain() # this fetches nearest expiration by default
    print(f"  ✅ yfinance RELIANCE: {len(opts.calls)} calls, {len(opts.puts)} puts")
except Exception as e:
    print(f"  ❌ yfinance RELIANCE failed: {e}")

# 2. Institutional Activity (Scraping)
print("\n[2] Testing FII/DII Scraping...")
try:
    url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    dfs = pd.read_html(response.content)
    
    # Usually the first table is the daily activity
    if dfs:
        fii_df = dfs[0]
        print(f"  ✅ Scraped FII/DII Data: {len(fii_df)} rows")
        print(fii_df.head(2))
    else:
        print("  ❌ No tables found on MoneyControl page")
        
except Exception as e:
    print(f"  ❌ Scraping failed: {e}")
