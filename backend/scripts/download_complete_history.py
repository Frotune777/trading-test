"""
Download Complete Historical Data from NSE
Downloads data from 1995 till date for all NIFTY 50 stocks
"""

import sys
sys.path.insert(0, '/app')

import sqlite3
import pandas as pd
import logging
from datetime import datetime, timedelta
from app.data_sources.nse_master_data import NSEMasterData

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# NIFTY 50 symbols
NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
    "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA",
    "TITAN", "ULTRACEMCO", "BAJFINANCE", "NESTLEIND", "WIPRO",
    "HCLTECH", "ONGC", "NTPC", "POWERGRID", "M&M",
    "TATAMOTORS", "TATASTEEL", "TECHM", "ADANIENT", "COALINDIA",
    "JSWSTEEL", "INDUSINDBK", "BAJAJFINSV", "GRASIM", "HINDALCO",
    "DRREDDY", "CIPLA", "EICHERMOT", "BRITANNIA", "DIVISLAB",
    "APOLLOHOSP", "BPCL", "TATACONSUM", "HEROMOTOCO", "SHRIRAMFIN",
    "SBILIFE", "ADANIPORTS", "LTIM", "BAJAJ-AUTO", "HDFCLIFE"
]


def download_complete_history(symbol: str, db_path: str = 'stock_data.db'):
    """
    Download complete historical data from 1995 till date
    
    Args:
        symbol: Stock symbol
        db_path: Database path
        
    Returns:
        Number of records stored
    """
    try:
        # Initialize NSE Master Data
        nse = NSEMasterData()
        nse.download_symbol_master()
        
        # Date range: 1995 to today
        start_date = datetime(1995, 1, 1)
        end_date = datetime.now()
        
        logger.info(f"Downloading {symbol} from {start_date.date()} to {end_date.date()}")
        
        # Fetch historical data (daily)
        df = nse.get_history(
            symbol=symbol,
            exchange='NSE',
            start=start_date,
            end=end_date,
            interval='1d'
        )
        
        if df is None or df.empty:
            logger.warning(f"No data received for {symbol}")
            return 0
        
        # Standardize columns
        df = df.reset_index()
        if 'Timestamp' in df.columns:
            df.rename(columns={'Timestamp': 'date'}, inplace=True)
        df.columns = [col.lower() for col in df.columns]
        
        # Remove timezone if present
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            if df['date'].dt.tz is not None:
                df['date'] = df['date'].dt.tz_localize(None)
        
        # Store in database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        records_stored = 0
        for _, row in df.iterrows():
            try:
                # Extract date
                date_val = row.get('date')
                if pd.isna(date_val):
                    continue
                
                # Convert to string format
                if isinstance(date_val, pd.Timestamp):
                    date_str = date_val.strftime('%Y-%m-%d')
                else:
                    date_str = str(date_val)
                
                # Insert or replace
                cursor.execute('''
                    INSERT OR REPLACE INTO price_history 
                    (symbol, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    date_str,
                    float(row.get('open', 0)),
                    float(row.get('high', 0)),
                    float(row.get('low', 0)),
                    float(row.get('close', 0)),
                    int(row.get('volume', 0))
                ))
                records_stored += 1
                
            except Exception as e:
                logger.debug(f"Error storing row for {symbol}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ {symbol}: Stored {records_stored} records")
        return records_stored
        
    except Exception as e:
        logger.error(f"❌ {symbol}: Error - {e}")
        return 0


def download_all_symbols():
    """Download complete history for all NIFTY 50 symbols"""
    
    logger.info("=" * 60)
    logger.info("DOWNLOADING COMPLETE HISTORICAL DATA (1995 - Present)")
    logger.info("=" * 60)
    
    results = {
        'total_symbols': len(NIFTY_50_SYMBOLS),
        'successful': 0,
        'failed': 0,
        'total_records': 0
    }
    
    for i, symbol in enumerate(NIFTY_50_SYMBOLS, 1):
        logger.info(f"\n[{i}/{len(NIFTY_50_SYMBOLS)}] Processing {symbol}...")
        
        records = download_complete_history(symbol)
        
        if records > 0:
            results['successful'] += 1
            results['total_records'] += records
        else:
            results['failed'] += 1
    
    logger.info("\n" + "=" * 60)
    logger.info("DOWNLOAD COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total symbols: {results['total_symbols']}")
    logger.info(f"Successful: {results['successful']}")
    logger.info(f"Failed: {results['failed']}")
    logger.info(f"Total records: {results['total_records']:,}")
    logger.info("=" * 60)
    
    return results


if __name__ == "__main__":
    results = download_all_symbols()
    
    # Verify database
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM price_history')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT symbol) FROM price_history')
    symbols = cursor.fetchone()[0]
    
    cursor.execute('SELECT symbol, COUNT(*), MIN(date), MAX(date) FROM price_history GROUP BY symbol ORDER BY COUNT(*) DESC LIMIT 10')
    
    print("\n=== DATABASE VERIFICATION ===")
    print(f"Total records: {total:,}")
    print(f"Unique symbols: {symbols}")
    print("\nTop 10 symbols by record count:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:,} records ({row[2]} to {row[3]})")
    
    conn.close()
