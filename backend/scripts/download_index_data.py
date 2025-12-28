"""
Download NIFTY Index Data from NSE to PostgreSQL

Downloads historical data for NIFTY 50 index and stores in PostgreSQL database as 'NIFTY'.
"""

import sys
sys.path.insert(0, '/app')

import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import text
from app.core.config import settings
from app.data_sources.nse_master_data import NSEMasterData

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def download_nifty_index():
    """Download NIFTY 50 index data"""
    logger.info("Initializing NSE Master Data...")
    nse = NSEMasterData()
    nse.download_symbol_master()
    
    # Create PostgreSQL engine
    pg_uri = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_SERVER}:5432/{settings.POSTGRES_DB}"
    )
    engine = create_async_engine(pg_uri, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    # Date range: 1 year
    end_date = datetime.now()
    start_date = datetime(end_date.year - 1, end_date.month, end_date.day)
    
    symbol = "Nifty 50"
    target_symbol = "NIFTY"
    
    logger.info(f"Downloading {symbol} from {start_date.date()} to {end_date.date()}...")
    
    try:
        # Fetch data from NSE
        df = nse.get_history(
            symbol=symbol,
            exchange='NSE',
            start=start_date,
            end=end_date,
            interval='1d'
        )
        
        if df is None or df.empty:
            logger.error(f"❌ No data received for {symbol}")
            return
        
        # Standardize columns
        df = df.reset_index()
        if 'Timestamp' in df.columns:
            df.rename(columns={'Timestamp': 'date'}, inplace=True)
        df.columns = [col.lower() for col in df.columns]
        
        # Ensure date column is datetime without timezone
        if 'date' in df.columns:
            import pandas as pd
            df['date'] = pd.to_datetime(df['date'])
            if hasattr(df['date'].dt, 'tz') and df['date'].dt.tz is not None:
                df['date'] = df['date'].dt.tz_localize(None)
        
        # Add symbol column
        df['symbol'] = target_symbol
        
        # Select only required columns
        required_cols = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
        df = df[[col for col in required_cols if col in df.columns]]
        
        # Convert to records
        records = df.to_dict('records')
        
        logger.info(f"Inserting {len(records)} records for {target_symbol} into PostgreSQL...")
        
        # Insert into PostgreSQL
        async with session_maker() as session:
            insert_sql = """
            INSERT INTO price_history (symbol, date, open, high, low, close, volume)
            VALUES (:symbol, :date, :open, :high, :low, :close, :volume)
            ON CONFLICT (symbol, date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume
            """
            
            await session.execute(text(insert_sql), records)
            await session.commit()
        
        logger.info(f"✅ {target_symbol}: Successfully inserted/updated {len(records)} records")
        
    except Exception as e:
        logger.error(f"❌ Error downloading {symbol}: {e}", exc_info=True)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(download_nifty_index())
