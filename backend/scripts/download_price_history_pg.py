"""
Download Historical Price Data from NSE to PostgreSQL

Downloads OHLCV data for NIFTY 50 stocks and stores in PostgreSQL database.
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


class PriceHistoryDownloader:
    """Download and store historical price data"""
    
    def __init__(self):
        self.nse = None
        self.engine = None
        self.session_maker = None
        
    async def initialize(self):
        """Initialize NSE client and database connection"""
        logger.info("Initializing NSE Master Data...")
        self.nse = NSEMasterData()
        self.nse.download_symbol_master()
        
        # Create PostgreSQL engine
        pg_uri = (
            f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_SERVER}:5432/{settings.POSTGRES_DB}"
        )
        self.engine = create_async_engine(pg_uri, echo=False)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)
        
        # Create price_history table if it doesn't exist
        await self.create_table()
        
    async def create_table(self):
        """Create price_history table in PostgreSQL"""
        statements = [
            """
            CREATE TABLE IF NOT EXISTS price_history (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                date DATE NOT NULL,
                open DECIMAL(12, 2),
                high DECIMAL(12, 2),
                low DECIMAL(12, 2),
                close DECIMAL(12, 2),
                volume BIGINT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(symbol, date)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_price_history_symbol ON price_history(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(date)",
            "CREATE INDEX IF NOT EXISTS idx_price_history_symbol_date ON price_history(symbol, date)"
        ]
        
        async with self.engine.begin() as conn:
            for stmt in statements:
                await conn.execute(text(stmt))
        
        logger.info("✅ price_history table created/verified")
    
    async def download_symbol_history(self, symbol: str, days: int = 365) -> int:
        """
        Download historical data for a symbol
        
        Args:
            symbol: Stock symbol
            days: Number of days of history (default: 365 = 1 year)
            
        Returns:
            Number of records inserted
        """
        try:
            # Date range
            end_date = datetime.now()
            start_date = datetime(end_date.year - (days // 365) - 1, end_date.month, end_date.day)
            
            logger.info(f"Downloading {symbol} from {start_date.date()} to {end_date.date()}")
            
            # Fetch data from NSE
            df = self.nse.get_history(
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
            
            # Ensure date column is datetime without timezone
            if 'date' in df.columns:
                import pandas as pd
                df['date'] = pd.to_datetime(df['date'])
                if hasattr(df['date'].dt, 'tz') and df['date'].dt.tz is not None:
                    df['date'] = df['date'].dt.tz_localize(None)
            
            # Add symbol column
            df['symbol'] = symbol
            
            # Select only required columns
            required_cols = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
            df = df[[col for col in required_cols if col in df.columns]]
            
            # Convert to records
            records = df.to_dict('records')
            
            if not records:
                logger.warning(f"No records to insert for {symbol}")
                return 0
            
            # Insert into PostgreSQL
            async with self.session_maker() as session:
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
            
            logger.info(f"✅ {symbol}: Inserted/Updated {len(records)} records")
            return len(records)
            
        except Exception as e:
            logger.error(f"❌ Error downloading {symbol}: {e}", exc_info=True)
            return 0
    
    async def download_all_nifty50(self, days: int = 365):
        """
        Download historical data for all NIFTY 50 stocks
        
        Args:
            days: Number of days of history (default: 365)
        """
        logger.info("=" * 60)
        logger.info("DOWNLOADING NIFTY 50 HISTORICAL DATA")
        logger.info("=" * 60)
        logger.info(f"Symbols: {len(NIFTY_50_SYMBOLS)}")
        logger.info(f"Days: {days}")
        logger.info("")
        
        total_records = 0
        successful = 0
        failed = 0
        
        for i, symbol in enumerate(NIFTY_50_SYMBOLS, 1):
            logger.info(f"[{i}/{len(NIFTY_50_SYMBOLS)}] Processing {symbol}...")
            
            records = await self.download_symbol_history(symbol, days)
            
            if records > 0:
                total_records += records
                successful += 1
            else:
                failed += 1
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total symbols: {len(NIFTY_50_SYMBOLS)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total records: {total_records:,}")
        logger.info("")
        
        # Verify data in database
        await self.verify_data()
    
    async def verify_data(self):
        """Verify downloaded data"""
        logger.info("Verifying data in database...")
        
        async with self.engine.connect() as conn:
            # Total records
            result = await conn.execute(text("SELECT COUNT(*) FROM price_history"))
            total = result.scalar()
            logger.info(f"Total records: {total:,}")
            
            # Records per symbol
            result = await conn.execute(text("""
                SELECT symbol, COUNT(*) as cnt, MIN(date) as min_date, MAX(date) as max_date
                FROM price_history
                GROUP BY symbol
                ORDER BY cnt DESC
                LIMIT 10
            """))
            
            logger.info("\nTop 10 symbols by record count:")
            for row in result:
                logger.info(f"  {row[0]:15} {row[1]:4} records  |  {row[2]} to {row[3]}")
        
        logger.info("\n✅ Data verification complete")
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()


async def main():
    """Main function"""
    downloader = PriceHistoryDownloader()
    
    try:
        await downloader.initialize()
        
        # Download 1 year of history for all NIFTY 50 stocks
        await downloader.download_all_nifty50(days=365)
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        await downloader.close()


if __name__ == "__main__":
    asyncio.run(main())
