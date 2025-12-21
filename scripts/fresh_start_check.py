import sys
import os
import shutil
import logging
from datetime import datetime

# Add parent dir to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.app.database.db_manager import DatabaseManager
from backend.app.database.updater import DataUpdater

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = 'stock_data.db'
BACKUP_PATH = f'stock_data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'

def reset_database():
    if os.path.exists(DB_PATH):
        logger.info(f"Backing up existing database to {BACKUP_PATH}...")
        shutil.move(DB_PATH, BACKUP_PATH)
    
    logger.info("Initializing fresh database...")
    # Initialize new DB
    db = DatabaseManager(DB_PATH)
    return db

def check_coverage(db: DatabaseManager, symbol: str):
    logger.info(f"\n📊 Data Coverage Report for {symbol}")
    logger.info("=" * 50)
    
    tables_to_check = [
        'companies', 
        'latest_snapshot',
        'price_history', 
        'quarterly_results', 
        'annual_results', 
        'balance_sheet', 
        'cash_flow', 
        'financial_ratios', # Checking if this is the correct name now
        'shareholding',
        'peers',
        'technical_indicators' # If any
    ]
    
    # Also check derivatives/market info if applicable, but focusing on core stock data first
    
    for table in tables_to_check:
        try:
            # Handle standard tables
            query = f"SELECT COUNT(*) as count FROM {table} WHERE symbol = ?"
            if table == 'companies':
                 # companies table might use 'symbol' as primary key, but query is same
                 pass
            
            # Check if table exists first (to avoid crashing script on missing tables)
            check_table = pd.read_sql_query(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'", db.conn)
            if check_table.empty:
                logger.warning(f"❌ Table '{table}' DOES NOT EXIST in schema.")
                continue

            df = pd.read_sql_query(query, db.conn, params=(symbol,))
            count = df.iloc[0]['count']
            
            if count > 0:
                logger.info(f"✅ {table}: {count} records")
                
                # Deep dive for specific critical tables
                if table == 'latest_snapshot':
                    snap = pd.read_sql_query(f"SELECT * FROM {table} WHERE symbol = ?", db.conn, params=(symbol,))
                    # Check for nulls in critical columns
                    crit_cols = ['pe_ratio', 'roe', 'market_cap', 'current_price']
                    nulls = [c for c in crit_cols if snap.iloc[0].get(c) is None]
                    if nulls:
                        logger.warning(f"   ⚠️ Missing fields in snapshot: {nulls}")
            else:
                logger.warning(f"❌ {table}: NO DATA")
                
        except Exception as e:
            logger.error(f"Error checking {table}: {e}")

    logger.info("=" * 50)

import pandas as pd

def main():
    # 1. Reset
    db = reset_database()
    
    # 2. Add Stock
    symbol = "TCS"
    logger.info(f"Adding {symbol}...")
    db.add_company(symbol, "Tata Consultancy Services Ltd.")
    
    # 3. Update
    logger.info(f"Triggering full update for {symbol}...")
    updater = DataUpdater(db_path=DB_PATH)
    result = updater.update_stock(symbol, force=True)
    
    if result['success']:
        logger.info("Update successful.")
    else:
        logger.error(f"Update failed: {result.get('errors')}")
        
    # 4. Check Coverage
    check_coverage(db, symbol)

if __name__ == "__main__":
    main()
