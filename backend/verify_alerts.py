import requests
import json
import logging

BASE_URL = "http://localhost:8000/api/v1"
SYMBOL = "RELIANCE"

logging.basicConfig(level=logging.INFO)

def test_alerts():
    # 1. Create Alert
    print("1. Creating Alert...")
    payload = {
        "symbol": SYMBOL,
        "alert_type": "CONVICTION_ABOVE",
        "threshold": 90,
        "channels": ["websocket"]
    }
    
    response = requests.post(f"{BASE_URL}/quad/alerts", json=payload)
    if response.status_code != 200:
        print(f"❌ Failed to create alert: {response.text}")
        return False
        
    alert = response.json()
    alert_id = alert['id']
    print(f"✅ Alert Created with ID: {alert_id}")
    
    # 2. List Alerts
    print("2. Listing Alerts...")
    response = requests.get(f"{BASE_URL}/quad/alerts?symbol={SYMBOL}")
    alerts = response.json()
    if len(alerts) > 0 and any(a['id'] == alert_id for a in alerts):
        print(f"✅ Alert found in list")
    else:
        print("❌ Alert not found in list")
        return False

    # 3. Delete Alert
    print("3. Deleting Alert...")
    response = requests.delete(f"{BASE_URL}/quad/alerts/{alert_id}")
    if response.status_code == 200:
        print("✅ Alert deleted")
    else:
        print(f"❌ Failed to delete alert: {response.text}")
        return False
        
    return True

if __name__ == "__main__":
    test_alerts()
