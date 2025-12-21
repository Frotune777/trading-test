import sys
import os
import logging
from pathlib import Path

# Add parent directory to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.app.database.updater import DataUpdater
from backend.app.database.db_manager import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def fill_data_gaps():
    print("🚀 Starting Data Gap Filling Process...")
    
    db = DatabaseManager('stock_data.db')
    updater = DataUpdater('stock_data.db')
    
    # Get all companies
    companies = db.get_all_companies()
    if not companies:
        print("❌ No companies found in database!")
        return

    symbols = [c['symbol'] for c in companies]
    print(f"📊 Found {len(symbols)} companies: {', '.join(symbols)}")
    
    success_count = 0
    
    for symbol in symbols:
        print(f"\n🔄 Processing {symbol}...")
        try:
            result = updater.update_stock(symbol, force=True)
            
            if result.get('success'):
                updates = [k for k, v in result['updates'].items() if 'success' in str(v)]
                print(f"✅ Success! Updated: {', '.join(updates)}")
                success_count += 1
            else:
                print(f"❌ Failed: {result.get('errors')}")
                
        except Exception as e:
            print(f"💥 Error processing {symbol}: {e}")
            
    print("\n🌍 Updating Market Data (FII/DII, Breadth)...")
    try:
        market_res = updater.update_market_data()
        print(f"✅ Market Data: {market_res['updates']}")
    except Exception as e:
        print(f"❌ Market Data Failed: {e}")

    print(f"\n✨ Completed! Updated {success_count}/{len(symbols)} stocks.")

if __name__ == "__main__":
    fill_data_gaps()
