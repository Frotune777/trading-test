"""
Insider Trading Data Collection Service
Fetches and stores insider trading data from NSE
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from app.data_sources.nse_utils import NseUtils

logger = logging.getLogger(__name__)


class InsiderTradingService:
    """
    Service to fetch and store NSE insider trading data
    """
    
    def __init__(self, db_manager=None):
        from app.database.db_manager import DatabaseManager
        self.db_manager = db_manager or DatabaseManager()
        self.nse_utils = NseUtils()
    
    def fetch_and_store(self, days: int = 30) -> Dict[str, Any]:
        """
        Fetch insider trading data for the last N days and store in database
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"Fetching insider trading data from {start_date.date()} to {end_date.date()}")
            
            # Fetch from NSE
            df = self.nse_utils.get_insider_trading(
                from_date=start_date.strftime('%d-%m-%Y'),
                to_date=end_date.strftime('%d-%m-%Y')
            )
            
            if df is None or df.empty:
                logger.warning("No insider trading data returned from NSE")
                return {
                    'status': 'no_data',
                    'records_fetched': 0,
                    'records_stored': 0
                }
            
            logger.info(f"Fetched {len(df)} insider trading records")
            
            # Store in database
            records_stored = self._store_data(df)
            
            logger.info(f"✅ Stored {records_stored} insider trading records")
            
            return {
                'status': 'success',
                'records_fetched': len(df),
                'records_stored': records_stored,
                'date_range': f"{start_date.date()} to {end_date.date()}"
            }
            
        except Exception as e:
            logger.error(f"Error fetching insider trading data: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'records_fetched': 0,
                'records_stored': 0
            }
    
    def _store_data(self, df: pd.DataFrame) -> int:
        """
        Store insider trading data in database (PostgreSQL via DatabaseManager)
        """
        records_stored = 0
        params_list = []
        
        for _, row in df.iterrows():
            try:
                # Parse acquisition date (transaction date)
                acq_from = row.get('acqfromDt', '')
                if pd.isna(acq_from) or acq_from == '-':
                    acquisition_date = None
                else:
                    try:
                        acquisition_date = datetime.strptime(acq_from, '%d-%b-%Y').date()
                    except:
                        acquisition_date = None
                
                # Parse intimation date
                intim_dt = row.get('intimDt', '')
                if pd.isna(intim_dt) or intim_dt == '-':
                    intimation_date = None
                else:
                    try:
                        intimation_date = datetime.strptime(intim_dt, '%d-%b-%Y').date()
                    except:
                        intimation_date = None
                
                # Helper to get value or None
                def get_val(key, default=None):
                    val = row.get(key, default)
                    if pd.isna(val) or val == '-':
                        return default
                    return val
                
                # Determine transaction type and shares
                buy_qty = get_val('buyQuantity', 0)
                sell_qty = get_val('sellquantity', 0)
                buy_val = get_val('buyValue', 0)
                sell_val = get_val('sellValue', 0)
                
                if buy_qty and buy_qty != 0:
                    transaction_type = 'buy'
                    shares = int(buy_qty)
                    value = float(buy_val) if buy_val else 0.0
                elif sell_qty and sell_qty != 0:
                    transaction_type = 'sell'
                    shares = int(sell_qty)
                    value = float(sell_val) if sell_val else 0.0
                else:
                    transaction_type = str(get_val('tdpTransactionType', 'unknown')).lower()
                    shares = 0
                    value = 0.0
                
                # Map to insider_trading table from schema.py
                params_list.append((
                    get_val('symbol'),
                    get_val('acqName'),
                    get_val('personCategory'),
                    get_val('secType'),
                    transaction_type,
                    shares,
                    value,
                    acquisition_date,
                    intimation_date
                ))
                records_stored += 1
                
            except Exception as e:
                logger.debug(f"Error preparing insider trading row: {e}")
                continue
        
        if params_list:
            # PostgreSQL compatible INSERT. 
            # Note: We should ideally have a unique constraint on (symbol, person_name, acquisition_date, transaction_type, number_of_securities)
            # For now, we just insert. Duplicate management should be handled by the unique constraint in schema.py.
            query = '''
                INSERT INTO insider_trading
                (symbol, person_name, person_category, securities_type,
                 transaction_type, number_of_securities, value,
                 acquisition_date, intimation_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            self.db_manager.executemany(query, params_list)
        
        return records_stored


# Standalone script for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    service = InsiderTradingService()
    
    print("\n=== FETCHING INSIDER TRADING DATA ===\n")
    results = service.fetch_and_store(days=30)
    
    print(f"\nStatus: {results['status']}")
    print(f"Records fetched: {results['records_fetched']}")
    print(f"Records stored: {results['records_stored']}")
    if 'date_range' in results:
        print(f"Date range: {results['date_range']}")
    
    # Verify database
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM insider_trading')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT symbol) FROM insider_trading')
    symbols = cursor.fetchone()[0]
    
    print(f"\n=== DATABASE VERIFICATION ===")
    print(f"Total records: {total:,}")
    print(f"Unique symbols: {symbols}")
    
    # Show sample
    cursor.execute('''
        SELECT symbol, person_name, acquisition_disposal, 
               acquired_disposed_shares, transaction_date
        FROM insider_trading
        ORDER BY transaction_date DESC
        LIMIT 5
    ''')
    print(f"\nLatest 5 transactions:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} - {row[2]} {row[3]:,} shares on {row[4]}")
    
    conn.close()
