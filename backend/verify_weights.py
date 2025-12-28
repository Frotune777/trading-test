import requests
import json
import logging

BASE_URL = "http://localhost:8000/api/v1"
SYMBOL = "RELIANCE"

logging.basicConfig(level=logging.INFO)

def test_weights():
    # 1. Get Initial Weights
    print("\n1. Getting Initial Weights...")
    try:
        response = requests.get(f"{BASE_URL}/preferences/weights")
        if response.status_code == 200:
            initial_weights = response.json()
            print(f"✅ Current Weights: {json.dumps(initial_weights, indent=2)}")
        else:
            print(f"❌ Failed to get weights: {response.text}")
            return False
            
        # 2. Set Custom Weights
        print("\n2. Setting Custom Weights (Trend=0.8, Momentum=0.2, others=0)...")
        new_weights = {
            'trend': 0.8,
            'momentum': 0.2,
            'volatility': 0.0,
            'liquidity': 0.0,
            'sentiment': 0.0,
            'regime': 0.0
        }
        
        response = requests.post(
            f"{BASE_URL}/preferences/weights", 
            json={"weights": new_weights}
        )
        
        if response.status_code == 200:
            print("✅ Custom weights set successfully")
        else:
            print(f"❌ Failed to set weights: {response.text}")
            return False
            
        # 3. Verify Persistence
        print("\n3. Verifying Persistence...")
        response = requests.get(f"{BASE_URL}/preferences/weights")
        current_weights = response.json()
        if current_weights.get('trend') == 0.8:
            print("✅ Weights persisted correctly")
        else:
            print(f"❌ Weights mismatch: {current_weights}")
            return False
            
        # 4. Trigger Analysis (to ensure engine accepts them)
        print("\n4. Triggering Analysis (Validation)...")
        # Using manual trigger to force analysis
        response = requests.post(f"{BASE_URL}/quad/analysis/{SYMBOL}")
        if response.status_code == 200:
            print("✅ Analysis completed with custom weights")
            # In a real deep check we'd verify the 'pillar_weights_snapshot' in response
            data = response.json()
            # print(json.dumps(data, indent=2))
        else:
            print(f"❌ Analysis failed: {response.text}")
            return False

        # 5. Reset Weights
        print("\n5. Resetting Weights...")
        response = requests.post(f"{BASE_URL}/preferences/reset")
        if response.status_code == 200:
            print("✅ Weights reset successfully")
        else:
            print(f"❌ Failed to reset weights: {response.text}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_weights()
