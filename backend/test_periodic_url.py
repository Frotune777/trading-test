from app.data_sources.nse_utils import NseUtils
import requests
import json

nse = NseUtils()

symbol = "TCS"
urls_to_test = [
    f"https://www.nseindia.com/api/historical/cm/equity?symbol={symbol}",
    f"https://www.nseindia.com/api/historical/cm/equity?symbol={symbol}&series=[\"EQ\"]&from=14-01-2025&to=14-01-2026", # Example date range 
    f"https://www.nseindia.com/api/quote-equity?symbol={symbol}&section=periodic",
]

print("--- Testing Candidate URLs for Periodic High/Low ---")

# Test Historical Data API specifically
print(f"\n--- Testing Historical Data API for {symbol} ---")

api_url = "https://www.nseindia.com/api/historical/cm/equity"
params = {
    "symbol": symbol,
    "series": '["EQ"]',
    "from": "14-01-2025",
    "to": "14-01-2026"
}

try:
    # 1. Ensure session is fresh
    nse._establish_session()
    
    # 2. Set Referer - critical for this API
    headers = nse.headers.copy()
    headers['Referer'] = f"https://www.nseindia.com/get-quote/equity?symbol={symbol}"
    
    # Testing Chart API which contains historical data
    # https://www.nseindia.com/api/chart-databyindex?index=TCS&indices=true (or similar)
    
    # Try 1: Standard chart endpoint
    encoded_url = f"https://www.nseindia.com/api/chart-databyindex?index={symbol}"
    print(f"Requesting Chart API: {encoded_url}")
    
    response = nse.session.get(encoded_url, headers=headers, cookies=nse.session.cookies.get_dict(), timeout=10)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success! Data keys:", list(data.keys()) if isinstance(data, dict) else "List")
        if "grapthData" in data and len(data["grapthData"]) > 0:
             print(f"Total Points: {len(data['grapthData'])}")
             print("First Point:", data["grapthData"][0])
             print("Last Point:", data["grapthData"][-1])
             # Check if it has timestamps
    else:
        print("Failed")
        print("Response:", response.text[:500])

except Exception as e:
    print(f"Exception: {e}")

