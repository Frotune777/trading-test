import sys
import os
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.app.services.unified_data_service import UnifiedDataService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_priority():
    service = UnifiedDataService()
    symbol = 'TCS'
    
    print(f"🚀 Fetching data for {symbol}...")
    data = service.get_comprehensive_data(symbol)
    
    print("\n📊 Verification Results:")
    
    # Check Company Info
    info = data.get('company_info', {})
    print(f"Company Name: {info.get('company_name')}")
    print(f"Sector: {info.get('sector')}")
    print(f"Industry: {info.get('industry')}")
    print(f"Full Info Keys: {list(info.keys())}")
    
    # Check Key Metrics
    metrics = data.get('key_metrics', {})
    print(f"\nKey Metrics Sample: {list(metrics.keys())[:5]}")
    print(f"PE Ratio: {metrics.get('pe_ratio')}")
    print(f"Market Cap: {metrics.get('market_cap')}")
    
    # Check Price Data
    price = data.get('price_data', {})
    print(f"\nPrice: {price.get('last_price')}")
    print(f"Source priority check (Upper Circuit present?): {'upper_circuit' in price}") # Specific to NseUtils

    if 'upper_circuit' in price:
        print("✅ NseUtils Price Data confirmed (Upper Circuit present)")
    else:
        print("⚠️ NseUtils Price Data missing?")

if __name__ == "__main__":
    verify_priority()
