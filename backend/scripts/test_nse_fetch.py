import requests
import pandas as pd
from datetime import datetime
import time

class NseFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Upgrade-Insecure-Requests': "1",
            "DNT": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Visit home page to get cookies
        print("Visiting NSE home page...")
        self.session.get("https://www.nseindia.com", timeout=10)
        
    def get_historical_data(self, symbol, from_date, to_date):
        # Format: dd-mm-yyyy
        url = "https://www.nseindia.com/api/historical/cm/equity"
        params = {
            "symbol": symbol,
            "series": '["EQ"]',
            "from": from_date,
            "to": to_date
        }
        
        try:
            print(f"Fetching data for {symbol} from {from_date} to {to_date}...")
            
            # NSE requires Referer header for API calls
            self.session.headers.update({
                'Referer': f'https://www.nseindia.com/get-quotes/equity?symbol={symbol}'
            })
            
            start_time = time.time()
            response = self.session.get(url, params=params, timeout=20)
            print(f"Request took {time.time() - start_time:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    print(f"Success! Retrieved {len(data['data'])} records")
                    for record in data['data'][:3]:
                        print(record)
                    return data['data']
                else:
                    print("No 'data' field in response")
                    # print(data) # Reduce noise
            else:
                print(f"Error: {response.status_code}")
                # print(response.text[:200])
                
        except Exception as e:
            print(f"Exception during fetch: {e}")
            
        return None

if __name__ == "__main__":
    fetcher = NseFetcher()
    # Try fetching last 3 months data
    fetcher.get_historical_data("TCS", "01-10-2025", "10-01-2026")
