import asyncio
import asyncpg
import pandas as pd
from datetime import datetime, timedelta
from nselib import capital_market
import yfinance as yf
import logging
import argparse
import sys
import os
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('download_history.log')
    ]
)
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

async def get_db_connection():
    return await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5438),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("POSTGRES_DB", "quad_trading")
    )

def fetch_nse_data(symbol, start_date, end_date):
    """
    Fetches data from NSE using nselib.
    Returns DataFrame or None.
    """
    try:
        from_str = start_date.strftime("%d-%m-%Y")
        to_str = end_date.strftime("%d-%m-%Y")
        
        # logger.debug(f"Calling nselib for {symbol} ({from_str} to {to_str})")
        df = capital_market.price_volume_and_deliverable_position_data(
            symbol=symbol, 
            from_date=from_str, 
            to_date=to_str
        )
        return df
    except Exception as e:
        # logger.debug(f"nselib fetch failed for {symbol}: {e}")
        return None

async def download_historical_data(source='nse'):
    """
    Downloads historical data for all companies in the DB.
    Source: 'nse' (nselib) or 'yfinance'
    """
    logger.info(f"Starting historical data download using source: {source.upper()}")
    
    conn = await get_db_connection()
    
    try:
        rows = await conn.fetch("SELECT symbol FROM companies ORDER BY symbol")
        companies = [row['symbol'] for row in rows]
        logger.info(f"Found {len(companies)} companies to process")
        
        for symbol in companies:
            logger.info(f"\nProcessing {symbol}...")
            
            # Determine start date
            last_date = await conn.fetchval(
                "SELECT MAX(timestamp) FROM historical_ohlc WHERE symbol = $1", 
                symbol
            )
            
            if last_date:
                # last_date is likely timezone aware if from DB
                if last_date.tzinfo is None:
                    last_date = IST.localize(last_date)
                    
                current_start = last_date + timedelta(days=1)
                logger.info(f"  Resuming from {current_start.date()}")
            else:
                current_start = IST.localize(datetime(2015, 1, 1))
                logger.info("  Starting fresh from 2015")
                
            end_date = datetime.now(IST)
            
            if current_start >= end_date:
                logger.info("  Data already up to date.")
                continue

            # Loop through chunks
            while current_start < end_date:
                # Use 180-day chunks to be safe with nselib
                chunk_end = current_start + timedelta(days=180)
                if chunk_end > end_date:
                    chunk_end = end_date
                
                # Skip if start >= end
                if current_start >= chunk_end:
                     break

                logger.info(f"  Fetching data for {symbol}: {current_start.strftime('%d-%m-%Y')} to {chunk_end.strftime('%d-%m-%Y')}")
                
                success = False
                
                # --- NSE (Primary) ---
                if source == 'nse':
                    try:
                        # Try plain symbol first
                        df = await asyncio.to_thread(fetch_nse_data, symbol, current_start, chunk_end)
                        
                        # If empty/None, try adding -EQ suffix (if not already present)
                        if (df is None or df.empty) and not symbol.endswith('-EQ'):
                             alt_symbol = f"{symbol}-EQ"
                             logger.info(f"    Retrying as {alt_symbol}...")
                             df = await asyncio.to_thread(fetch_nse_data, alt_symbol, current_start, chunk_end)

                        if df is not None and not df.empty:
                            # Process NSE data
                            records = []
                            for _, row in df.iterrows():
                                try:
                                    # Parse Date and Localize to IST
                                    ts_naive = pd.to_datetime(row['Date'])
                                    ts = IST.localize(ts_naive)
                                    
                                    # Safe extraction helper
                                    def safe_float(val):
                                        if pd.isna(val) or str(val).strip() == '-': return None
                                        return float(str(val).replace(',', ''))
                                    
                                    def safe_int(val):
                                        if pd.isna(val) or str(val).strip() == '-': return None
                                        return int(str(val).replace(',', ''))

                                    # Parse numeric columns with safety
                                    rec = {
                                        'symbol': symbol, # Store as original symbol
                                        'timestamp': ts,
                                        'open': safe_float(row['OpenPrice']),
                                        'high': safe_float(row['HighPrice']),
                                        'low': safe_float(row['LowPrice']),
                                        'close': safe_float(row['ClosePrice']),
                                        'volume': safe_int(row['TotalTradedQuantity']) or 0,
                                        'delivery_quantity': safe_int(row.get('DeliverableQty')),
                                        'delivery_percentage': safe_float(row.get('%DlyQttoTradedQty')),
                                        'source': 'nse'
                                    }
                                    
                                    if rec['close'] is not None:
                                        records.append(rec)
                                except Exception as e:
                                    # logger.warning(f"    Skipping row {row['Date']} due to error: {e}")
                                    continue

                            if records:
                                # Batch Insert
                                # Added interval='1d' and exchange='NSE'
                                # Updated ON CONFLICT to appropriate constraint
                                await conn.executemany("""
                                    INSERT INTO historical_ohlc 
                                    (symbol, timestamp, open, high, low, close, volume, delivery_quantity, delivery_percentage, source, interval, exchange)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, '1d', 'NSE')
                                    ON CONFLICT (symbol, exchange, interval, timestamp) 
                                    DO UPDATE SET 
                                        close = EXCLUDED.close,
                                        volume = EXCLUDED.volume,
                                        delivery_quantity = EXCLUDED.delivery_quantity,
                                        delivery_percentage = EXCLUDED.delivery_percentage,
                                        source = EXCLUDED.source
                                """, [
                                    (
                                        r['symbol'], r['timestamp'], r['open'], r['high'], r['low'], 
                                        r['close'], r['volume'], r['delivery_quantity'], r['delivery_percentage'], r['source']
                                    ) for r in records
                                ])
                                logger.info(f"  ✅ NSE: Inserted {len(records)} records")
                                success = True
                        else:
                            logger.warning("  ⚠️ NSE: No data found")

                    except Exception as e:
                        logger.error(f"  NSE Batch Error: {e}")

                # --- Yahoo Finance (Fallback - Last Resort) ---
                if not success:
                    logger.info("  ⚠️ NSE failed/skipped, trying yfinance fallback (LAST RESORT)...")
                    try:
                        yf_symbol = f"{symbol}.NS"
                        ticker = yf.Ticker(yf_symbol)
                        # yfinance expects YYYY-MM-DD
                        hist = await asyncio.to_thread(ticker.history, start=current_start.date(), end=(chunk_end + timedelta(days=1)).date())
                        
                        if not hist.empty:
                            records = []
                            for ts, row in hist.iterrows():
                                 # yfinance returns timezone-aware timestamps (usually)
                                 # Ensure it matches DB expectation
                                 if ts.tzinfo is None:
                                     ts = IST.localize(ts)
                                 else:
                                     ts = ts.astimezone(IST)

                                 records.append((
                                    symbol, ts, 
                                    float(row['Open']), float(row['High']), float(row['Low']), float(row['Close']), int(row['Volume']),
                                    None, None, 'yfinance' # No delivery data
                                ))
                            
                            # Added interval='1d' and exchange='NSE' (even for yahoo)
                            await conn.executemany("""
                                INSERT INTO historical_ohlc 
                                (symbol, timestamp, open, high, low, close, volume, delivery_quantity, delivery_percentage, source, interval, exchange)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, '1d', 'NSE')
                                ON CONFLICT (symbol, exchange, interval, timestamp) DO NOTHING
                            """, records)
                            logger.info(f"  ✅ yfinance: Inserted {len(records)} records")
                            success = True
                        else:
                            logger.warning("  ❌ yfinance: No data found either")

                    except Exception as e:
                        logger.error(f"  yfinance Batch Error: {e}")

                # Move to next chunk
                current_start = chunk_end + timedelta(days=1)
                # Add a small delay to avoid rate limits
                await asyncio.sleep(1.0)
                
    finally:
        await conn.close()
    
    logger.info("Historical data download complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download historical data')
    parser.add_argument('--source', type=str, default='nse', help='Source: nse or yfinance')
    args = parser.parse_args()
    
    try:
        asyncio.run(download_historical_data(source=args.source))
    except KeyboardInterrupt:
        logger.info("Script interrupted by user.")
    except Exception as e:
        logger.error(f"Script error: {e}")
