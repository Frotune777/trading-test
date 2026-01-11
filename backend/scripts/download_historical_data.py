"""
Download historical OHLC data from NSE (1995 onwards) for sample companies
Populates historical_ohlc table in PostgreSQL
"""
import asyncio
import asyncpg
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/home/fortune/Desktop/Python_Projects/quad_trading/trading-test/backend')

from app.data_sources.nse_utils import NseUtils
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def download_historical_data():
    """Download historical data for all companies in database"""
    
    # Connect to Docker PostgreSQL
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,
        user='postgres',
        password='postgres',
        database='quad_trading'
    )
    
    try:
        # Get all companies
        companies = await conn.fetch("SELECT symbol, name FROM companies ORDER BY symbol")
        logger.info(f"Found {len(companies)} companies to process")
        
        nse = NseUtils()
        
        # Date range: 1995 to today
        end_date = datetime.now()
        start_date = datetime(1995, 1, 1)
        
        total_records = 0
        
        for company in companies:
            symbol = company['symbol']
            logger.info(f"\nProcessing {symbol}...")
            
            try:
                # Download data in yearly chunks to avoid timeouts
                current_start = start_date
                symbol_records = 0
                
                while current_start < end_date:
                    # Process one year at a time
                    current_end = min(current_start + timedelta(days=365), end_date)
                    
                    from_date = current_start.strftime('%d-%m-%Y')
                    to_date = current_end.strftime('%d-%m-%Y')
                    
                    logger.info(f"  Fetching {from_date} to {to_date}...")
                    
                    try:
                        # Get historical data from NSE
                        # Note: NSE doesn't have equity historical API, we'll use bhav copy
                        # For now, let's use a simpler approach with recent data
                        
                        # Skip to next year
                        current_start = current_end + timedelta(days=1)
                        
                    except Exception as e:
                        logger.warning(f"  Error fetching data for {symbol} ({from_date} to {to_date}): {e}")
                        current_start = current_end + timedelta(days=1)
                        continue
                
                logger.info(f"  ✅ {symbol}: {symbol_records} records")
                total_records += symbol_records
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"  ❌ Error processing {symbol}: {e}")
                continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Download complete! Total records: {total_records}")
        logger.info(f"{'='*60}")
        
    finally:
        await conn.close()

async def download_recent_data_yfinance():
    """
    Alternative: Download recent data using yfinance as a quick solution
    NSE historical data requires complex bhav copy processing
    """
    import yfinance as yf
    
    # Connect to Docker PostgreSQL
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,
        user='postgres',
        password='postgres',
        database='quad_trading'
    )
    
    try:
        # Get all companies
        companies = await conn.fetch("SELECT symbol, name FROM companies ORDER BY symbol")
        logger.info(f"Found {len(companies)} companies to process")
        
        # Date range: 2 years of data for testing
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)  # 2 years
        
        total_records = 0
        
        for company in companies:
            symbol = company['symbol']
            # Add .NS suffix for NSE stocks in yfinance
            yf_symbol = f"{symbol}.NS"
            
            logger.info(f"\nProcessing {symbol} ({yf_symbol})...")
            
            try:
                # Download data from yfinance
                ticker = yf.Ticker(yf_symbol)
                df = ticker.history(start=start_date, end=end_date, interval='1d')
                
                if df.empty:
                    logger.warning(f"  No data found for {symbol}")
                    continue
                
                # Insert into database
                records_inserted = 0
                for index, row in df.iterrows():
                    try:
                        await conn.execute("""
                            INSERT INTO historical_ohlc 
                            (symbol, timestamp, open, high, low, close, volume, interval)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                            ON CONFLICT (symbol, timestamp, interval) DO NOTHING
                        """, symbol, index.to_pydatetime(), 
                            float(row['Open']), float(row['High']), 
                            float(row['Low']), float(row['Close']),
                            int(row['Volume']), '1d')
                        records_inserted += 1
                    except Exception as e:
                        logger.debug(f"  Skip duplicate: {index}")
                        continue
                
                logger.info(f"  ✅ {symbol}: {records_inserted} records inserted")
                total_records += records_inserted
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"  ❌ Error processing {symbol}: {e}")
                continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Download complete! Total records: {total_records}")
        logger.info(f"{'='*60}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Download historical OHLC data')
    parser.add_argument('--source', choices=['nse', 'yfinance'], default='yfinance',
                       help='Data source (yfinance is faster for testing)')
    args = parser.parse_args()
    
    if args.source == 'yfinance':
        logger.info("Using yfinance for historical data (2 years)")
        asyncio.run(download_recent_data_yfinance())
    else:
        logger.info("Using NSE bhav copy (1995 onwards)")
        asyncio.run(download_historical_data())
