"""
Phase 3 Data Migration Script
Consolidates Fragmented SQLite OHLC tables into a Unified PostgreSQL Data Lake.
"""

import os
import sqlite3
import pandas as pd
import logging
import json
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SQLITE_DB_PATH = "/home/fortune/Desktop/Python_Projects/trader_start/data/trading.db"
POSTGRES_URI = "postgresql://postgres:postgres@localhost:5438/quad_trading"

class Phase3Migrator:
    def __init__(self):
        self.sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        self.sqlite_conn.row_factory = sqlite3.Row
        self.engine = create_engine(POSTGRES_URI)
        self.Session = sessionmaker(bind=self.engine)

    def get_ohlc_tables(self) -> List[str]:
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_ohlc'")
        return [row[0] for row in cursor.fetchall()]

    def parse_table_name(self, table_name: str) -> (str, str):
        """Extract symbol and interval from table name e.g. sbin_1d_ohlc"""
        parts = table_name.split('_')
        # name pattern: symbol_interval_ohlc or symbol_part1_part2_interval_ohlc
        # usually symbol_interval_ohlc
        if len(parts) >= 3:
            interval = parts[-2]
            symbol = "_".join(parts[:-2]).upper()
            return symbol, interval
        return table_name.upper(), "1d"

    def migrate_ohlc_and_indicators(self, table_name: str):
        symbol, interval = self.parse_table_name(table_name)
        logger.info(f"Processing {table_name} -> Symbol: {symbol}, Interval: {interval}")
        
        df = pd.read_sql(f"SELECT * FROM {table_name}", self.sqlite_conn)
        if df.empty:
            return

        # Normalize column names
        df.columns = [c.capitalize() if c.lower() in ['open', 'high', 'low', 'close', 'volume'] else c for c in df.columns]
        if 'Datetime' not in df.columns:
             for c in df.columns:
                 if c.lower() == 'datetime':
                     df.rename(columns={c: 'Datetime'}, inplace=True)
                     break

        standard_cols = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
        indicator_cols = [c for c in df.columns if c not in standard_cols]

        batch_size = 5000
        for i in range(0, len(df), batch_size):
            chunk = df.iloc[i:i+batch_size]
            
            # Prepare data for bulk insert
            price_records = []
            indicator_records = []
            
            for _, row in chunk.iterrows():
                try:
                    ts = pd.to_datetime(row['Datetime'])
                    if pd.isnull(ts): continue
                except:
                    continue
                    
                price_records.append({
                    "symbol": symbol,
                    "exchange": "NSE",
                    "interval": interval,
                    "timestamp": ts,
                    "open": row.get('Open'),
                    "high": row.get('High'),
                    "low": row.get('Low'),
                    "close": row.get('Close'),
                    "volume": int(row.get('Volume', 0)) if pd.notnull(row.get('Volume')) else 0,
                    "source": "migrated_sqlite"
                })
                
                if indicator_cols:
                    indicators_payload = {c: row[c] for c in indicator_cols if pd.notnull(row[c])}
                    if indicators_payload:
                        indicator_records.append({
                            "symbol": symbol,
                            "interval": interval,
                            "timestamp": ts,
                            "indicators": json.dumps(indicators_payload)
                        })

            # Bulk Insert OHLC
            with self.Session() as session:
                if price_records:
                    price_sql = text("""
                        INSERT INTO historical_ohlc (symbol, exchange, interval, timestamp, open, high, low, close, volume, source)
                        VALUES (:symbol, :exchange, :interval, :timestamp, :open, :high, :low, :close, :volume, :source)
                        ON CONFLICT (symbol, exchange, interval, timestamp) DO UPDATE 
                        SET open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low, close = EXCLUDED.close, volume = EXCLUDED.volume
                    """)
                    session.execute(price_sql, price_records)
                
                if indicator_records:
                    indicator_sql = text("""
                        INSERT INTO indicator_history (symbol, interval, timestamp, indicators)
                        VALUES (:symbol, :interval, :timestamp, :indicators)
                        ON CONFLICT (symbol, interval, timestamp) DO UPDATE SET indicators = EXCLUDED.indicators
                    """)
                    session.execute(indicator_sql, indicator_records)
                
                session.commit()
            
            logger.info(f"  Inserted bulk batch {i//batch_size + 1} for {symbol} ({len(price_records)} rows)")

    def clean_numeric(self, val):
        if pd.isnull(val): return 0
        s = str(val).strip().replace(',', '')
        if s in ['-', 'Nil', 'null', 'None', '']: return 0
        try:
            return float(s)
        except:
            return 0

    def migrate_market_data(self):
        tables = ['market_bulk_deals', 'market_insider_trading', 'market_fii_dii']
        for table in tables:
            logger.info(f"Migrating market data table: {table}")
            df = pd.read_sql(f"SELECT * FROM {table}", self.sqlite_conn)
            if df.empty:
                continue
                
            with self.Session() as session:
                if table == 'market_bulk_deals':
                    for _, row in df.iterrows():
                        sql = text("""
                            INSERT INTO market_bulk_deals (date, order_type, symbol, scrip_name, client_name, buy_sell, quantity, price, remarks)
                            VALUES (:date, :order_type, :symbol, :scrip_name, :client_name, :buy_sell, :quantity, :price, :remarks)
                        """)
                        try:
                            dt = pd.to_datetime(row.get('BD_DT_DATE'))
                        except:
                            dt = None
                            
                        session.execute(sql, {
                            "date": dt,
                            "order_type": row.get('BD_DT_ORDER'),
                            "symbol": row.get('BD_SYMBOL'),
                            "scrip_name": row.get('BD_SCRIP_NAME'),
                            "client_name": row.get('BD_CLIENT_NAME'),
                            "buy_sell": row.get('BD_BUY_SELL'),
                            "quantity": self.clean_numeric(row.get('BD_QTY_TRD')),
                            "price": self.clean_numeric(row.get('BD_TP_WATP')),
                            "remarks": row.get('BD_REMARKS')
                        })
                elif table == 'market_fii_dii':
                    for _, row in df.iterrows():
                        sql = text("""
                            INSERT INTO market_fii_dii (date, category, buy_value, sell_value, net_value)
                            VALUES (:date, :category, :buy_value, :sell_value, :net_value)
                        """)
                        try:
                             dt = pd.to_datetime(row.get('date'))
                        except:
                             dt = None
                        session.execute(sql, {
                            "date": dt,
                            "category": row.get('category'),
                            "buy_value": self.clean_numeric(row.get('buyValue')),
                            "sell_value": self.clean_numeric(row.get('sellValue')),
                            "net_value": self.clean_numeric(row.get('netValue'))
                        })
                elif table == 'market_insider_trading':
                    for _, row in df.iterrows():
                        sql = text("""
                            INSERT INTO market_insider_trading (symbol, company, person_name, person_category, transaction_type, securities_type, number_of_securities, value, acquisition_date)
                            VALUES (:symbol, :company, :person_name, :person_category, :transaction_type, :securities_type, :number_of_securities, :value, :acquisition_date)
                        """)
                        try:
                             dt = pd.to_datetime(row.get('acqfromDt'))
                        except:
                             dt = None
                        session.execute(sql, {
                            "symbol": row.get('symbol'),
                            "company": row.get('company'),
                            "person_name": row.get('acqName'),
                            "person_category": row.get('personCategory'),
                            "transaction_type": row.get('tdpTransactionType'),
                            "securities_type": row.get('secType'),
                            "number_of_securities": int(self.clean_numeric(row.get('buyQuantity')) or self.clean_numeric(row.get('sellquantity'))),
                            "value": self.clean_numeric(row.get('buyValue')) or self.clean_numeric(row.get('sellValue')),
                            "acquisition_date": dt
                        })
                session.commit()

    def migrate_metadata(self):
        logger.info("Migrating metadata...")
        df = pd.read_sql("SELECT * FROM ohlcv_metadata", self.sqlite_conn)
        with self.Session() as session:
            for _, row in df.iterrows():
                sql = text("""
                    INSERT INTO ohlcv_metadata (symbol, exchange, interval, earliest_available, latest_available, total_records, last_sync)
                    VALUES (:symbol, :exchange, :interval, :earliest_available, :latest_available, :total_records, :last_sync)
                    ON CONFLICT (symbol, exchange, interval) DO UPDATE SET 
                        earliest_available = EXCLUDED.earliest_available,
                        latest_available = EXCLUDED.latest_available,
                        total_records = EXCLUDED.total_records,
                        last_sync = EXCLUDED.last_sync
                """)
                session.execute(sql, {
                    "symbol": row['symbol'],
                    "exchange": "NSE",
                    "interval": row['timeframe'],
                    "earliest_available": pd.to_datetime(row['first_date']),
                    "latest_available": pd.to_datetime(row['last_date']),
                    "total_records": row['record_count'],
                    "last_sync": pd.to_datetime(row['last_updated'])
                })
            session.commit()

    def run(self):
        logger.info("Starting Phase 3 Migration...")
        # 1. Metadata
        self.migrate_metadata()
        
        # 2. OHLC Tables
        tables = self.get_ohlc_tables()
        for table in tables:
            self.migrate_ohlc_and_indicators(table)
            
        # 3. Market Data (Institutional Activity)
        self.migrate_market_data() 
        
        logger.info("Phase 3 Migration Completed.")

if __name__ == "__main__":
    migrator = Phase3Migrator()
    migrator.run()
