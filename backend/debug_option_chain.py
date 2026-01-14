import requests
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.nseindia.com/option-chain'
}

s = requests.Session()

def init_session():
    print("Initializing session...")
    # 1. Visit Home
    s.get("https://www.nseindia.com", headers=headers, timeout=10)
    # 2. Visit Option Chain Page to set specific cookies
    s.get("https://www.nseindia.com/option-chain", headers=headers, timeout=10)
    print(f"Cookies: {s.cookies.get_dict()}")

def test_endpoint(name, url):
    print(f"\n--- Testing {name} ---")
    print(f"URL: {url}")
    try:
        r = s.get(url, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            try:
                data = r.json()
                keys = list(data.keys())
                print(f"Success! Keys: {keys}")
                if 'records' in data:
                    print(f"Records count: {len(data['records'].get('data', []))}")
            except:
                print("Not JSON content")
                print(r.text[:200])
        else:
            print("Failed")
            print(r.text[:200])
    except Exception as e:
        print(f"Error: {e}")

init_session()
test_endpoint("Option Chain Equities (TCS)", "https://www.nseindia.com/api/option-chain-equities?symbol=TCS")
test_endpoint("Option Chain Indices (NIFTY)", "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY")
