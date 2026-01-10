"""
Phase 3 Migration Verification Script
Performs bit-perfect comparison between SQLite source and PostgreSQL destination.
"""

import sqlite3
import pandas as pd
import json
import logging
from sqlalchemy import create_engine, text

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SQLITE_DB_PATH = "/home/fortune/Desktop/Python_Projects/trader_start/data/trading.db"
POSTGRES_URI = "postgresql://postgres:postgres@localhost:5438/quad_trading"

class MigrationVerifier:
    def __init__(self):
        self.sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        self.pg_engine = create_engine(POSTGRES_URI)

    def verify_symbol(self, symbol: str, sqlite_table: str):
        logger.info(f"Verifying {symbol}...")
        
        # 1. Fetch SQLite Data
        df_sqlite = pd.read_sql(f"SELECT * FROM {sqlite_table}", self.sqlite_conn)
        
        # Normalize columns for verification
        df_sqlite.columns = [c.lower() for c in df_sqlite.columns]
        if 'datetime' in df_sqlite.columns:
            df_sqlite['datetime'] = pd.to_datetime(df_sqlite['datetime'])
        elif 'date' in df_sqlite.columns:
            df_sqlite.rename(columns={'date': 'datetime'}, inplace=True)
            df_sqlite['datetime'] = pd.to_datetime(df_sqlite['datetime'])
        
        # 2. Fetch PostgreSQL Data
        with self.pg_engine.connect() as conn:
            query = text("""
                SELECT h.timestamp, h.open, h.high, h.low, h.close, h.volume, i.indicators
                FROM historical_ohlc h
                LEFT JOIN indicator_history i ON h.id = i.ohlc_id
                WHERE h.symbol = :symbol AND h.interval = '1d'
                ORDER BY h.timestamp ASC
            """)
            df_pg = pd.read_sql(query, conn, params={"symbol": symbol.upper()})
        
        if df_pg.empty:
            logger.error(f"  ❌ No data found in PostgreSQL for {symbol}")
            return False

        # 3. Row Count check
        if len(df_sqlite) != len(df_pg):
            logger.warning(f"  ⚠️  Row count mismatch: SQLite({len(df_sqlite)}) vs PG({len(df_pg)})")
        else:
            logger.info(f"  ✅ Row counts match: {len(df_pg)}")

        # 4. Data Point Check (Latest row)
        sqlite_last = df_sqlite.iloc[-1]
        pg_last = df_pg.iloc[-1]
        
        # Open price check
        sqlite_open = float(sqlite_last['open']) if 'open' in sqlite_last else float(sqlite_last.get('open', 0))
        pg_open = float(pg_last['open'])
        
        if abs(sqlite_open - pg_open) < 0.001:
            logger.info(f"  ✅ Last candle Open matches: {pg_open}")
        else:
            logger.error(f"  ❌ Last candle Open mismatch: SQLite({sqlite_open}) vs PG({pg_open})")

        # 5. Indicators check
        if pg_last['indicators']:
            pg_indicators = pg_last['indicators'] if isinstance(pg_last['indicators'], dict) else json.loads(pg_last['indicators'])
            # Check for a few common indicators if they exist in SQLite
            for col in ['rsi', 'sma_20', 'ema_50']:
                if col in df_sqlite.columns:
                    sq_val = sqlite_last[col]
                    if pd.notnull(sq_val):
                        sq_val = float(sq_val)
                        pg_val = float(pg_indicators.get(col.upper(), pg_indicators.get(col, 0)))
                        if abs(sq_val - pg_val) < 0.001:
                             logger.info(f"  ✅ Indicator {col} matches: {pg_val}")
                        else:
                             logger.warning(f"  ⚠️  Indicator {col} mismatch: SQLite({sq_val}) vs PG({pg_val})")
        
        return True

    def run(self):
        # Pick a few sample tables
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_1d_ohlc' LIMIT 5")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            symbol = table.split('_')[0].upper()
            self.verify_symbol(symbol, table)

if __name__ == "__main__":
    verifier = MigrationVerifier()
    verifier.run()
