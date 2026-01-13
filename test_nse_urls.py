import requests
import logging

logging.basicConfig(level=logging.INFO)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

s = requests.Session()
s.headers.update(headers)

# 1. Init cookies
try:
    print("Initializing...")
    s.get("https://www.nseindia.com", timeout=10)
except Exception as e:
    print(f"Init failed: {e}")

urls_to_test = [
    # Old
    "https://www.nseindia.com/get-quotes/equity?symbol=TCS",
    # New attempts
    "https://www.nseindia.com/get-quote/equity?symbol=TCS",
    "https://www.nseindia.com/get-quote/equity/TCS",
    # Detailed New
    "https://www.nseindia.com/get-quote/equity/TCS/Tata-Consultancy-Services-Limited"
]



print("\n--- Derivatives / Option Chain Test ---")
symbol = "TCS"

# 1. Existing Code Logic
ref_url_deriv = 'https://www.nseindia.com/get-quotes/derivatives?symbol=' + symbol
print(f"Fetching Deriv Ref (Old): {ref_url_deriv}")
try:
    ref = s.get(ref_url_deriv, timeout=10)
    print(f"Ref Final URL: {ref.url}")
    print(f"Ref Status: {ref.status_code}")
except Exception as e:
    print(f"Deriv Ref Failed: {e}")

# 2. API Call for Option Chain
api_url_oc = f'https://www.nseindia.com/api/option-chain-equities?symbol={symbol}'
print(f"Fetching API: {api_url_oc}")
try:
    r_api = s.get(api_url_oc, cookies=ref.cookies, timeout=10)
    print(f"API Status: {r_api.status_code}")
    if r_api.status_code == 200:
        data = r_api.json()
        if "records" in data:
            print(f"Old Logic Success! Records: {len(data.get('records', {}).get('data', []))}")
        else:
             print("Old Logic: Missing records")
except Exception as e:
    print(f"API Failed: {e}")


print("\n--- Strategy Test: Discover Slug & Construct URL ---")
# 1. Hit Equity to find slug
base_ref_url = 'https://www.nseindia.com/get-quotes/equity?symbol=' + symbol
print(f"Base Ref: {base_ref_url}")
r_base = s.get(base_ref_url, timeout=10)
final_base_url = r_base.url
print(f"Redirected to: {final_base_url}")

# 2. Construct Option Chain URL
# Expecting format: .../get-quote/equity/TCS/Slug --> .../get-quote/optionchain/TCS/Slug
if "/get-quote/equity/" in final_base_url:
    target_referer = final_base_url.replace("/get-quote/equity/", "/get-quote/optionchain/")
    print(f"Constructed Option Chain Referer: {target_referer}")
    
    # 3. Test if this Referer is valid (returns 200)
    try:
        r_oc_page = s.get(target_referer, timeout=10)
        print(f"Option Chain Page Status: {r_oc_page.status_code}")
    except Exception as e:
        print(f"Failed to fetch OC Page: {e}")
        
    # 4. Use this Referer for API call
    headers_opt = s.headers.copy()
    headers_opt['Referer'] = target_referer
    print("Calling API with new Referer...")
    try:
        r_api = s.get(api_url_oc, headers=headers_opt, cookies=r_base.cookies, timeout=10)
        print(f"API with correct Referer Status: {r_api.status_code}")
        if r_api.status_code == 200:
            data = r_api.json()
            if "records" in data:
                 print("Keys found: 'records'")
                 if "data" in data["records"]:
                     print("Keys found: 'records' -> 'data'")
                     rows = data["records"]["data"]
                     print(f"Number of rows: {len(rows)}")
                 else:
                     print("Missing 'data' in 'records'")
            else:
                 print("Missing 'records' in response")
                 print(f"Response Keys: {list(data.keys())}")

    except Exception as e:
        print(f"API Failed: {e}")
else:
    print("Failed to parse base URL structure.")
