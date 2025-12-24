import requests
import json

def test_endpoint(url):
    print(f"Testing {url}...")
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response (text): {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_endpoint("http://localhost:8000/api/v1/market/status")
    test_endpoint("http://localhost:8000/api/v1/recommendations/RELIANCE/reasoning")
    test_endpoint("http://localhost:8000/api/v1/insider/sentinel/RELIANCE")
