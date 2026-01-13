from nselib import capital_market
import pandas as pd
from datetime import date, timedelta

try:
    print("Fetching data using nselib...")
    # Get last 30 days
    to_date = date.today().strftime("%d-%m-%Y")
    from_date = (date.today() - timedelta(days=30)).strftime("%d-%m-%Y")
    
    print(f"Fetching TCS data from {from_date} to {to_date}")
    
    # nselib uses dd-mm-yyyy format
    df = capital_market.price_volume_and_deliverable_position_data(symbol='TCS', from_date=from_date, to_date=to_date)
    
    print(f"Success! Retrieved {len(df)} records")
    print(df.head())
    print(df.columns)
    
except Exception as e:
    print(f"Error: {e}")
