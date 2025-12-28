import requests
import json
import logging

BASE_URL = "http://localhost:8000/api/v1"
SYMBOL = "RELIANCE"

logging.basicConfig(level=logging.INFO)

def test_trade_setup():
    url = f"{BASE_URL}/trade-signals/{SYMBOL}/setup"
    print(f"Testing Trade Setup: {url}")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("✅ Trade Setup Response Valid")
            # print(json.dumps(data, indent=2))
            
            # Verify critical fields
            if "pivots" in data and "zones" in data and "position_sizing" in data:
                print("✅ All required fields present")
                
                sizing = data['position_sizing']
                print(f"   Recommended Shares: {sizing['recommended_shares']}")
                print(f"   Kelly Allocation: {sizing['kelly_allocation_pct']}%")
                
                zones = data['zones']
                print(f"   Support Zones: {len(zones['support'])}")
                print(f"   Resistance Zones: {len(zones['resistance'])}")
            else:
                 print("❌ Missing fields in response")
                 
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_trade_setup()
