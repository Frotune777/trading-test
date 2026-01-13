import requests
import logging
import json

logging.basicConfig(level=logging.INFO)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Referer': 'https://www.nseindia.com/get-quote/equity?symbol=TCS'
}

s = requests.Session()
s.headers.update(headers)

# 1. Init cookies
try:
    print("Initializing...")
    s.get("https://www.nseindia.com", timeout=10)
except Exception as e:
    print(f"Init failed: {e}")

# 2. Test User's URL
target_url = "https://www.nseindia.com/api/NextApi/apiClient/GetQuoteApi?functionName=getSymbolData&marketType=N&series=EQ&symbol=TCS"

print(f"\nTesting URL: {target_url}")
try:
    r = s.get(target_url, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Headers: {r.headers}")
    if r.status_code == 200:
        try:
            data = r.json()
            print("Success! JSON Keys:", list(data.keys()))
            # Save to file for inspection
            with open("nextapi_response.json", "w") as f:
                json.dump(data, f, indent=2)
            print("Saved response to nextapi_response.json")
        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            print("Response text preview:", r.text[:200])
    else:
        print("Response text preview:", r.text[:200])
except Exception as e:
    print(f"Failed: {e}")
