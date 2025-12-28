"""
Calculate and Store Technical Indicators using TA-Lib

Automatically calculates technical indicators after price data is downloaded.
Stores in PostgreSQL for fast access.
"""

import sys
sys.path.insert(0, '/app')

import asyncio
import logging
import numpy as np
import pandas as pd
import talib
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import text, select
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TechnicalIndicatorCalculator:
    """Calculate and store technical indicators"""
    
    def __init__(self):
        self.engine = None
        self.session_maker = None
        
    async def initialize(self):
        """Initialize database connection"""
        pg_uri = (
            f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_SERVER}:5432/{settings.POSTGRES_DB}"
        )
        self.engine = create_async_engine(pg_uri, echo=False)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)
        
        await self.create_table()
        
    async def create_table(self):
        """Create technical_indicators table"""
        statements = [
            """
            CREATE TABLE IF NOT EXISTS technical_indicators (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                date DATE NOT NULL,
                
                -- Moving Averages
                sma_20 DECIMAL(12, 2),
                sma_50 DECIMAL(12, 2),
                sma_200 DECIMAL(12, 2),
                ema_12 DECIMAL(12, 2),
                ema_26 DECIMAL(12, 2),
                
                -- MACD
                macd DECIMAL(12, 4),
                macd_signal DECIMAL(12, 4),
                macd_hist DECIMAL(12, 4),
                
                -- RSI
                rsi_14 DECIMAL(10, 2),
                
                -- Bollinger Bands
                bb_upper DECIMAL(12, 2),
                bb_middle DECIMAL(12, 2),
                bb_lower DECIMAL(12, 2),
                bb_bandwidth DECIMAL(10, 4),
                
                -- Stochastic
                stoch_k DECIMAL(10, 2),
                stoch_d DECIMAL(10, 2),
                
                -- ADX (Trend Strength)
                adx DECIMAL(10, 2),
                plus_di DECIMAL(10, 2),
                minus_di DECIMAL(10, 2),
                
                -- ATR (Volatility)
                atr_14 DECIMAL(12, 2),
                
                -- Volume Indicators
                obv BIGINT,
                
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(symbol, date)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_tech_indicators_symbol ON technical_indicators(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_tech_indicators_date ON technical_indicators(date)",
            "CREATE INDEX IF NOT EXISTS idx_tech_indicators_symbol_date ON technical_indicators(symbol, date)"
        ]
        
        async with self.engine.begin() as conn:
            for stmt in statements:
                await conn.execute(text(stmt))
        
        logger.info("✅ technical_indicators table created/verified")
    
    async def get_price_data(self, symbol: str) -> pd.DataFrame:
        """Fetch price history for a symbol"""
        async with self.engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT date, open, high, low, close, volume
                FROM price_history
                WHERE symbol = :symbol
                ORDER BY date ASC
            """), {"symbol": symbol})
            
            rows = result.fetchall()
            
            if not rows:
                return pd.DataFrame()
            
            df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            return df
    
    async def calculate_indicators(self, symbol: str) -> int:
        """
        Calculate all technical indicators for a symbol
        
        Returns:
            Number of records calculated
        """
        try:
            logger.info(f"Calculating indicators for {symbol}...")
            
            # Get price data
            df = await self.get_price_data(symbol)
            
            if df.empty or len(df) < 200:
                logger.warning(f"Insufficient data for {symbol}: {len(df)} records")
                return 0
            
            # Convert to numpy arrays for TA-Lib
            open_prices = df['open'].astype(float).values
            high_prices = df['high'].astype(float).values
            low_prices = df['low'].astype(float).values
            close_prices = df['close'].astype(float).values
            volume = df['volume'].astype(float).values
            
            # Calculate Moving Averages
            df['sma_20'] = talib.SMA(close_prices, timeperiod=20)
            df['sma_50'] = talib.SMA(close_prices, timeperiod=50)
            df['sma_200'] = talib.SMA(close_prices, timeperiod=200)
            df['ema_12'] = talib.EMA(close_prices, timeperiod=12)
            df['ema_26'] = talib.EMA(close_prices, timeperiod=26)
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(
                close_prices,
                fastperiod=12,
                slowperiod=26,
                signalperiod=9
            )
            df['macd'] = macd
            df['macd_signal'] = macd_signal
            df['macd_hist'] = macd_hist
            
            # RSI
            df['rsi_14'] = talib.RSI(close_prices, timeperiod=14)
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(
                close_prices,
                timeperiod=20,
                nbdevup=2,
                nbdevdn=2,
                matype=0
            )
            df['bb_upper'] = bb_upper
            df['bb_middle'] = bb_middle
            df['bb_lower'] = bb_lower
            df['bb_bandwidth'] = (bb_upper - bb_lower) / bb_middle
            
            # Stochastic
            stoch_k, stoch_d = talib.STOCH(
                high_prices,
                low_prices,
                close_prices,
                fastk_period=14,
                slowk_period=3,
                slowk_matype=0,
                slowd_period=3,
                slowd_matype=0
            )
            df['stoch_k'] = stoch_k
            df['stoch_d'] = stoch_d
            
            # ADX (Trend Strength)
            df['adx'] = talib.ADX(high_prices, low_prices, close_prices, timeperiod=14)
            df['plus_di'] = talib.PLUS_DI(high_prices, low_prices, close_prices, timeperiod=14)
            df['minus_di'] = talib.MINUS_DI(high_prices, low_prices, close_prices, timeperiod=14)
            
            # ATR (Volatility)
            df['atr_14'] = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)
            
            # OBV (Volume)
            df['obv'] = talib.OBV(close_prices, volume)
            
            # Add symbol
            df['symbol'] = symbol
            
            # Select columns for database
            indicator_cols = [
                'symbol', 'date', 'sma_20', 'sma_50', 'sma_200', 'ema_12', 'ema_26',
                'macd', 'macd_signal', 'macd_hist', 'rsi_14',
                'bb_upper', 'bb_middle', 'bb_lower', 'bb_bandwidth',
                'stoch_k', 'stoch_d', 'adx', 'plus_di', 'minus_di', 'atr_14', 'obv'
            ]
            
            df_indicators = df[indicator_cols].copy()
            
            # Remove rows with NaN (first 200 rows typically)
            df_indicators = df_indicators.dropna()
            
            if df_indicators.empty:
                logger.warning(f"No valid indicators for {symbol}")
                return 0
            
            # Convert to records
            records = df_indicators.to_dict('records')
            
            # Insert into database
            async with self.session_maker() as session:
                insert_sql = """
                INSERT INTO technical_indicators (
                    symbol, date, sma_20, sma_50, sma_200, ema_12, ema_26,
                    macd, macd_signal, macd_hist, rsi_14,
                    bb_upper, bb_middle, bb_lower, bb_bandwidth,
                    stoch_k, stoch_d, adx, plus_di, minus_di, atr_14, obv
                )
                VALUES (
                    :symbol, :date, :sma_20, :sma_50, :sma_200, :ema_12, :ema_26,
                    :macd, :macd_signal, :macd_hist, :rsi_14,
                    :bb_upper, :bb_middle, :bb_lower, :bb_bandwidth,
                    :stoch_k, :stoch_d, :adx, :plus_di, :minus_di, :atr_14, :obv
                )
                ON CONFLICT (symbol, date) DO UPDATE SET
                    sma_20 = EXCLUDED.sma_20,
                    sma_50 = EXCLUDED.sma_50,
                    sma_200 = EXCLUDED.sma_200,
                    ema_12 = EXCLUDED.ema_12,
                    ema_26 = EXCLUDED.ema_26,
                    macd = EXCLUDED.macd,
                    macd_signal = EXCLUDED.macd_signal,
                    macd_hist = EXCLUDED.macd_hist,
                    rsi_14 = EXCLUDED.rsi_14,
                    bb_upper = EXCLUDED.bb_upper,
                    bb_middle = EXCLUDED.bb_middle,
                    bb_lower = EXCLUDED.bb_lower,
                    bb_bandwidth = EXCLUDED.bb_bandwidth,
                    stoch_k = EXCLUDED.stoch_k,
                    stoch_d = EXCLUDED.stoch_d,
                    adx = EXCLUDED.adx,
                    plus_di = EXCLUDED.plus_di,
                    minus_di = EXCLUDED.minus_di,
                    atr_14 = EXCLUDED.atr_14,
                    obv = EXCLUDED.obv
                """
                
                await session.execute(text(insert_sql), records)
                await session.commit()
            
            logger.info(f"✅ {symbol}: Calculated {len(records)} indicator records")
            return len(records)
            
        except Exception as e:
            logger.error(f"❌ Error calculating indicators for {symbol}: {e}", exc_info=True)
            return 0
    
    async def calculate_all_symbols(self):
        """Calculate indicators for all symbols in price_history"""
        logger.info("=" * 60)
        logger.info("CALCULATING TECHNICAL INDICATORS")
        logger.info("=" * 60)
        
        # Get unique symbols
        async with self.engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT DISTINCT symbol
                FROM price_history
                ORDER BY symbol
            """))
            symbols = [row[0] for row in result.fetchall()]
        
        logger.info(f"Found {len(symbols)} symbols")
        logger.info("")
        
        total_records = 0
        successful = 0
        failed = 0
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"[{i}/{len(symbols)}] {symbol}")
            
            records = await self.calculate_indicators(symbol)
            
            if records > 0:
                total_records += records
                successful += 1
            else:
                failed += 1
            
            # Small delay
            await asyncio.sleep(0.1)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("CALCULATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total symbols: {len(symbols)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total indicator records: {total_records:,}")
        logger.info("")
        
        await self.verify_data()
    
    async def verify_data(self):
        """Verify calculated indicators"""
        logger.info("Verifying indicators in database...")
        
        async with self.engine.connect() as conn:
            # Total records
            result = await conn.execute(text("SELECT COUNT(*) FROM technical_indicators"))
            total = result.scalar()
            logger.info(f"Total indicator records: {total:,}")
            
            # Sample data
            result = await conn.execute(text("""
                SELECT symbol, COUNT(*) as cnt, MIN(date) as min_date, MAX(date) as max_date
                FROM technical_indicators
                GROUP BY symbol
                ORDER BY cnt DESC
                LIMIT 10
            """))
            
            logger.info("\nTop 10 symbols by indicator count:")
            for row in result:
                logger.info(f"  {row[0]:15} {row[1]:4} records  |  {row[2]} to {row[3]}")
        
        logger.info("\n✅ Indicator verification complete")
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()


async def main():
    """Main function"""
    calculator = TechnicalIndicatorCalculator()
    
    try:
        await calculator.initialize()
        await calculator.calculate_all_symbols()
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        await calculator.close()


if __name__ == "__main__":
    asyncio.run(main())
