import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
SYMBOLS = ["RELIANCE", "INFY", "TCS", "INDOSTAR"]

ENDPOINTS = [
    ("/market/breadth", {}),
    ("/market/activity/volume", {}),
    ("/market/activity/value", {}),
    ("/market/indices", {}),
    ("/derivatives/option-chain/RELIANCE", {}),
    ("/derivatives/futures/RELIANCE", {}),
    ("/derivatives/pcr/RELIANCE", {}),
    ("/technicals/indicators/RELIANCE", {}),
    ("/technicals/intraday/RELIANCE?interval=5m", {}),
    ("/insider/trades", {}),
    ("/insider/bulk-deals", {}),
    ("/insider/block-deals", {}),
    ("/insider/short-selling", {}),
    ("/insider/sentinel/INDOSTAR", {}),
    ("/recommendations/", {}),
    ("/recommendations/RELIANCE/reasoning", {}),
]

def fetch_all():
    results = {}
    for path, params in ENDPOINTS:
        url = f"{BASE_URL}{path}"
        print(f"Fetching: {url}")
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                results[path] = resp.json()
            else:
                results[path] = {"error": f"Status {resp.status_code}", "detail": resp.text}
        except Exception as e:
            results[path] = {"error": str(e)}
    
    with open("api_audit_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    fetch_all()
