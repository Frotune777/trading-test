
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List, Optional
from app.database.db_manager import DatabaseManager
from app.data_sources.yahoo_finance import YahooFinance

logger = logging.getLogger(__name__)

class DataIngestionService:
    """
    Service for manual ingestion of market data from external sources.
    Handles fetching, validation, and idempotent persistence.
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.yahoo = YahooFinance()
        
    async def ingest_market_data(self, 
                               symbol: str, 
                               source: str, 
                               start_date: str, 
                               end_date: str, 
                               timeframe: str = '1d') -> Dict[str, Any]:
        """
        Ingest market data for a symbol from a specified source.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            source: Data source ('yahoo', 'openalgo')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Data timeframe (default '1d')
            
        Returns:
            Dictionary with ingestion summary
        """
        logger.info(f"Starting ingestion for {symbol} from {start_date} to {end_date} via {source}")
        
        # 1. Fetch Data
        df = self._fetch_data(symbol, source, start_date, end_date, timeframe)
        
        if df is None or df.empty:
            return {
                "symbol": symbol,
                "status": "failed",
                "message": "No data returned from source",
                "rows_fetched": 0,
                "rows_inserted": 0,
                "rows_skipped": 0
            }
            
        rows_fetched = len(df)
        
        # 2. Persist Data using SQLAlchemy (PostgreSQL)
        try:
            from app.core.database import SessionLocal
            from app.database.models_historical import HistoricalOHLC
            from sqlalchemy import select
            
            async with SessionLocal() as db:
                inserted = 0
                updated = 0
                
                for _, row in df.iterrows():
                    # Convert date to datetime with UTC timezone
                    if isinstance(row['date'], str):
                        from datetime import datetime
                        dt = datetime.strptime(row['date'], '%Y-%m-%d')
                    else:
                        dt = row['date']
                    
                    if not dt.tzinfo:
                        from datetime import timezone
                        dt = dt.replace(tzinfo=timezone.utc)
                    
                    # Check if record exists
                    stmt = select(HistoricalOHLC).where(
                        HistoricalOHLC.symbol == symbol,
                        HistoricalOHLC.exchange == "NSE",
                        HistoricalOHLC.interval == "1d",
                        HistoricalOHLC.timestamp == dt
                    )
                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        # Update existing record
                        existing.open = float(row['open'])
                        existing.high = float(row['high'])
                        existing.low = float(row['low'])
                        existing.close = float(row['close'])
                        existing.volume = int(row['volume'])
                        updated += 1
                    else:
                        # Insert new record
                        ohlc = HistoricalOHLC(
                            symbol=symbol,
                            exchange="NSE",
                            interval="1d",
                            timestamp=dt,
                            open=float(row['open']),
                            high=float(row['high']),
                            low=float(row['low']),
                            close=float(row['close']),
                            volume=int(row['volume']),
                            source=source
                        )
                        db.add(ohlc)
                        inserted += 1
                
                await db.commit()
                logger.info(f"✅ {symbol}: Inserted {inserted}, Updated {updated}")
            
            # Get date range from dataframe
            start_dt = df['date'].min()
            end_dt = df['date'].max()
            if isinstance(start_dt, pd.Timestamp):
                start_dt = start_dt.strftime('%Y-%m-%d')
            if isinstance(end_dt, pd.Timestamp):
                end_dt = end_dt.strftime('%Y-%m-%d')
            
            return {
                "symbol": symbol,
                "status": "success",
                "source": source,
                "timeframe": timeframe,
                "rows_fetched": rows_fetched,
                "rows_inserted": inserted,
                "rows_updated": updated,
                "date_range": [start_dt, end_dt]
            }
            
        except Exception as e:
            logger.error(f"Failed to persist data for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "status": "error",
                "message": str(e),
                "rows_fetched": rows_fetched,
                "rows_inserted": 0
            }

    def _fetch_data(self, symbol: str, source: str, start_date: str, end_date: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Fetch data from the chosen source."""
        if source.lower() == 'yahoo':
            # Yahoo finance fetch
            # Note: YahooFinance.get_historical_prices usually takes 'period' (1y, 1mo) or start/end
            # The current YahooFinance implementation in this codebase takes `period`.
            # We might need to extend it or use yfinance library directly for start/end if the wrapper is limited.
            # Let's check wrapper: get_historical_prices(self, symbol: str, period: str = '1y', interval: str = '1d')
            
            # Since the wrapper is limited to period, we'll try to calculate the period 
            # OR ideally use yfinance directly here for precision if the wrapper is too rigid.
            # Given the wrapper is simple, let's use yfinance Ticker directly here for exact date range control.
            
            try:
                import yfinance as yf
                ticker = yf.Ticker(f"{symbol}.NS")
                df = ticker.history(start=start_date, end=end_date, interval=timeframe)
                
                if df.empty:
                    return None
                    
                df = df.reset_index()
                # Rename columns to match what DatabaseManager expects (lowercase)
                df.columns = [col.lower() for col in df.columns]
                
                # Ensure date column exists (yfinance might name it Date or index)
                if 'date' not in df.columns and 'index' in df.columns:
                    df = df.rename(columns={'index': 'date'})
                    
                # Ensure strictly correct columns
                cols = ['date', 'open', 'high', 'low', 'close', 'volume']
                available_cols = [c for c in cols if c in df.columns]
                return df[available_cols]
                
            except Exception as e:
                logger.error(f"Error fetching from Yahoo directly: {e}")
                return None
                
        else:
            raise ValueError(f"Unsupported data source: {source}")

    async def get_data_availability(self, symbol: str) -> Dict[str, Any]:
        """
        Check existing data availability in the database.
        Returns the min and max date, and count of rows.
        """
        try:
            # We can use a direct query for speed
            query = """
                SELECT 
                    MIN(date) as start_date, 
                    MAX(date) as end_date, 
                    COUNT(*) as count 
                FROM price_history 
                WHERE symbol = ?
            """
            result = self.db.query_dict(query, (symbol,))
            
            if not result or result[0]['count'] == 0:
                 return {
                    "symbol": symbol,
                    "has_data": False,
                    "start_date": None,
                    "end_date": None,
                    "count": 0
                }
            
            return {
                "symbol": symbol,
                "has_data": True,
                "start_date": result[0]['start_date'],
                "end_date": result[0]['end_date'],
                "count": result[0]['count']
            }
            
        except Exception as e:
            logger.error(f"Error checking availability for {symbol}: {e}")
            return {"error": str(e)}

