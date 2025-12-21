import sys
import os
import logging

# Add parent dir to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.app.database.updater import DataUpdater
from backend.app.database.db_manager import DatabaseManager

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify():
    db_path = "stock_data.db" # Use default path
    updater = DataUpdater(db_path)
    db = DatabaseManager(db_path)
    
    symbol = "TCS"
    
    print("1. Testing Corporate Actions (Bulk Update)...")
    try:
        updater.update_all_corporate_actions()
        # Verify DB
        cursor = db.conn.cursor()
        cursor.execute("SELECT count(*) FROM corporate_actions")
        count = cursor.fetchone()[0]
        print(f"   => Saved {count} corporate actions.")
        
        cursor.execute("SELECT * FROM corporate_actions LIMIT 1")
        row = cursor.fetchone()
        if row:
            print(f"   Sample: {row}")
    except Exception as e:
        print(f"   ERROR: {e}")

    print(f"\n2. Testing Stock Update for {symbol} (Derivatives + Technicals)...")
    try:
        # We need to ensure price history exists for Technicals
        # forcing update to fetch price and then calc technicals
        updater.update_stock(symbol, force=True)
        
        # Verify Option Chain
        cursor.execute("SELECT count(*) FROM option_chain WHERE symbol=?", (symbol,))
        oc_count = cursor.fetchone()[0]
        print(f"   => Option Chain records for {symbol}: {oc_count}")
        
        # Verify Technicals
        cursor.execute("SELECT count(*) FROM technical_indicators WHERE symbol=?", (symbol,))
        ta_count = cursor.fetchone()[0]
        print(f"   => Technical Indicators for {symbol}: {ta_count}")
        
        if ta_count > 0:
            cursor.execute("SELECT * FROM technical_indicators WHERE symbol=? ORDER BY date DESC LIMIT 1", (symbol,))
            print(f"   Sample TA: {cursor.fetchone()}")
            
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    verify()
