import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"
SYMBOL = "RELIANCE"

def test_endpoint(name, url, method="GET", data=None):
    print(f"Testing {name}...", end=" ")
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
            
        if response.status_code == 200:
            print("✅ OK")
            # print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"❌ Failed ({response.status_code})")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print(f"🚀 Verifying Phase 2 Endpoint Implementation for {SYMBOL}\n")
    
    # 1. Peer Comparison
    test_endpoint(
        "Peer Comparison", 
        f"{BASE_URL}/quad/{SYMBOL}/peers"
    )
    
    # 2. Backtest
    test_endpoint(
        "Backtest & Equity Curve", 
        f"{BASE_URL}/quad/{SYMBOL}/backtest"
    )
    
    # 3. ML Prediction (Mock input)
    pillars = {
        "trend": 75,
        "momentum": 80,
        "volatility": 60,
        "liquidity": 90,
        "sentiment": 70,
        "regime": 50
    }
    test_endpoint(
        "ML Prediction", 
        f"{BASE_URL}/quad/{SYMBOL}/predict?days_ahead=7",
        method="POST",
        data=pillars
    )

if __name__ == "__main__":
    main()
