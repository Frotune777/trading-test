# /home/fortune/Desktop/Python_Projects/fortune_trading/tests/conftest.py
import unittest.mock as mock
import pandas as pd
from datetime import datetime

# --- Mock Data Fixtures ---
MOCK_NSE_PRICE_DATA = {
    # This mock structure must match what your fixed NSEComplete.get_price_data returns
    'price': {'current': 100.50, 'open': 100.00, 'high': 102.00, 'low': 99.50},
    'timestamp': str(datetime.now())
}
MOCK_HISTORICAL_DF = pd.DataFrame({
    'Open': [100, 101, 102],
    'High': [102, 103, 104],
    'Low': [99, 100, 101],
    'Close': [101, 102, 103],
    'Volume': [1000, 1200, 1500]
}, index=pd.to_datetime(['2025-01-01', '2025-01-02', '2025-01-03']))

# Utility to mock external requests
def mock_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.cookies = {} # Required for NSE
        def json(self):
            return self.json_data
        def raise_for_status(self):
            if self.status_code != 200:
                raise Exception("Mock HTTP Error")
        def keys(self):
            return []
            
    if 'get_price_data' in args[0]:
        return MockResponse(MOCK_NSE_PRICE_DATA, 200)
    
    return MockResponse({}, 200)