"""
Option Chain Data Collection Service
Fetches and stores option chain data from NSE for NIFTY 50 stocks
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, List
from app.data_sources.nse_utils import NseUtils

logger = logging.getLogger(__name__)


class OptionChainService:
    """
    Service to fetch and store NSE option chain data
    """
    
    # NIFTY 50 stocks with active options
    FNO_SYMBOLS = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
        "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA",
        "TITAN", "ULTRACEMCO", "BAJFINANCE", "NESTLEIND", "WIPRO",
        "HCLTECH", "ONGC", "NTPC", "POWERGRID", "M&M",
        "TATAMOTORS", "TATASTEEL", "TECHM", "ADANIENT", "COALINDIA",
        "JSWSTEEL", "INDUSINDBK", "BAJAJFINSV", "GRASIM", "HINDALCO",
        "DRREDDY", "CIPLA", "EICHERMOT", "BRITANNIA", "DIVISLAB",
        "APOLLOHOSP", "BPCL", "TATACONSUM", "HEROMOTOCO"
    ]
    
    def __init__(self, db_manager=None):
        from app.database.db_manager import DatabaseManager
        self.db_manager = db_manager or DatabaseManager()
        self.nse_utils = NseUtils()
    
    def fetch_and_store(self, symbols: List[str] = None) -> Dict[str, Any]:
        """
        Fetch option chain data for given symbols
        """
        if symbols is None:
            symbols = self.FNO_SYMBOLS
        
        total_fetched = 0
        total_stored = 0
        successful = 0
        failed = 0
        
        logger.info(f"Fetching option chain for {len(symbols)} symbols")
        
        for symbol in symbols:
            try:
                df = self.nse_utils.get_option_chain(symbol, indices=False)
                
                if df is None or df.empty:
                    logger.debug(f"No option chain data for {symbol}")
                    failed += 1
                    continue
                
                total_fetched += len(df)
                stored = self._store_data(symbol, df)
                total_stored += stored
                successful += 1
                
                logger.debug(f"✅ {symbol}: Stored {stored} option records")
                
            except Exception as e:
                logger.error(f"Error fetching option chain for {symbol}: {e}")
                failed += 1
                continue
        
        logger.info(f"✅ Option chain fetch complete: {successful}/{len(symbols)} successful")
        
        return {
            'status': 'success' if successful > 0 else 'no_data',
            'symbols_processed': len(symbols),
            'successful': successful,
            'failed': failed,
            'records_fetched': total_fetched,
            'records_stored': total_stored
        }
    
    def _store_data(self, symbol: str, df: pd.DataFrame) -> int:
        """
        Store option chain data in database (PostgreSQL via DatabaseManager)
        """
        records_stored = 0
        timestamp = datetime.now()
        
        params_list = []
        
        for _, row in df.iterrows():
            try:
                # Helper to get value or None
                def get_val(key, default=None):
                    val = row.get(key, default)
                    if pd.isna(val) or val is None:
                        return default
                    return val
                
                # Parse expiry date
                expiry = get_val('expiryDate')
                if expiry:
                    try:
                        expiry_date = datetime.strptime(expiry, '%d-%b-%Y').date()
                    except:
                        expiry_date = None
                else:
                    expiry_date = None
                
                # Insert parameters
                params_list.append((
                    symbol,
                    expiry_date,
                    float(get_val('strikePrice', 0)),
                    get_val('instrumentType'),  # CE or PE
                    int(get_val('openInterest', 0)),
                    int(get_val('changeinOpenInterest', 0)),
                    int(get_val('totalTradedVolume', 0)),
                    float(get_val('impliedVolatility', 0)),
                    float(get_val('lastPrice', 0)),
                    float(get_val('bidprice', 0)),
                    float(get_val('askPrice', 0)),
                    timestamp
                ))
                records_stored += 1
                
            except Exception as e:
                logger.debug(f"Error preparing option row for {symbol}: {e}")
                continue
        
        if params_list:
            # Note: Using parameterized SQL for PostgreSQL.
            # We use ON CONFLICT to mimic REPLACE behavior.
            # Target columns for unique constraint: (symbol, expiry_date, strike_price, option_type, timestamp)
            # Actually, timestamp is part of unique constraint in some schemas, let's check.
            query = '''
                INSERT INTO option_chain
                (symbol, expiry_date, strike_price, option_type,
                 open_interest, change_in_oi, volume, iv,
                 ltp, bid_price, ask_price, "timestamp")
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (symbol, expiry_date, strike_price, option_type, "timestamp") 
                DO UPDATE SET
                    open_interest = EXCLUDED.open_interest,
                    change_in_oi = EXCLUDED.change_in_oi,
                    volume = EXCLUDED.volume,
                    iv = EXCLUDED.iv,
                    ltp = EXCLUDED.ltp,
                    bid_price = EXCLUDED.bid_price,
                    ask_price = EXCLUDED.ask_price
            '''
            self.db_manager.executemany(query, params_list)
        
        return records_stored


# Standalone script for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    service = OptionChainService()
    
    print("\n=== FETCHING OPTION CHAIN DATA ===\n")
    # Test with just a few symbols
    test_symbols = ["RELIANCE", "TCS", "INFY"]
    results = service.fetch_and_store(symbols=test_symbols)
    
    print(f"\nStatus: {results['status']}")
    print(f"Symbols processed: {results['symbols_processed']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Records fetched: {results['records_fetched']}")
    print(f"Records stored: {results['records_stored']}")
    
    # Verify database
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM option_chain')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT symbol) FROM option_chain')
    symbols = cursor.fetchone()[0]
    
    print(f"\n=== DATABASE VERIFICATION ===")
    print(f"Total records: {total:,}")
    print(f"Unique symbols: {symbols}")
    
    conn.close()
