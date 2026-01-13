import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta
import json
from sqlalchemy import text
from app.core.database import sync_engine
from .schema import CREATE_TABLES, ALL_TABLES

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage PostgreSQL database operations (Consolidated from SQLite)."""
    
    def __init__(self, db_path: str = None):
        # db_path is ignored now as we use sync_engine from core
        self.engine = sync_engine
        # Schema initialization disabled - using migrations instead
        # self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database and create tables."""
        try:
            with self.engine.connect() as conn:
                # PostgreSQL doesn't need PRAGMA foreign_keys
                # Simple translation of SQLite-isms to PostgreSQL-isms in raw SQL
                pg_sql = CREATE_TABLES.replace("AUTOINCREMENT", "")
                pg_sql = pg_sql.replace("REAL", "DOUBLE PRECISION")
                pg_sql = pg_sql.replace("DATETIME", "TIMESTAMP")
                
                # Execute each statement (SQLAlchemy doesn't support multiple statements in one execute() usually)
                # Split by semicolon and filter out empty strings
                for statement in pg_sql.split(";"):
                    if statement.strip():
                        conn.execute(text(statement))
                
                conn.commit()
                logger.info("✅ PostgreSQL Database initialized and schemas applied")
                
                # Verify tables
                self._verify_schema(conn)
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def _verify_schema(self, conn):
        """Verify all tables exists in PostgreSQL."""
        query = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        result = conn.execute(query)
        existing_tables = [row[0] for row in result.fetchall()]
        
        missing = set(ALL_TABLES) - set(existing_tables)
        if missing:
            logger.warning(f"Missing tables in PostgreSQL: {missing}")
        else:
            logger.info(f"✅ All {len(ALL_TABLES)} tables verified in PostgreSQL")
    
    def execute(self, query: str, params: tuple = None, fetch_all: bool = False) -> Any:
        """
        Execute a SQL query using SQLAlchemy.
        
        Args:
            query: SQL query
            params: Tuple of parameters
            fetch_all: If True, fetches all results and returns list of rows/dicts. 
                       If False, returns ResultProxy (careful with closed connections).
        """
        try:
            # Simple param conversion from ? to :param for legacy queries
            if "?" in query and params:
                for i in range(len(params)):
                    query = query.replace("?", f":p{i}", 1)
                new_params = {f"p{i}": v for i, v in enumerate(params)}
            else:
                new_params = params or {}

            with self.engine.connect() as conn:
                result = conn.execute(text(query), new_params)
                conn.commit()
                if fetch_all or query.strip().upper().startswith("SELECT"):
                    return result.fetchall()
                return result
        except Exception as e:
            logger.error(f"SQL error: {e}\nQuery: {query}")
            raise

    def commit(self):
        """Legacy commit method - no-op as we use atomic transactions or auto-commit in execute."""
        pass
        
    def rollback(self):
        """Legacy rollback method - no-op as we use atomic transactions."""
        pass

    # ==================== DATE / TIME ====================

    def get_last_timestamp(self, symbol: str, table: str) -> Optional[datetime]:
        """Get last timestamp for a symbol in a table."""
        query = f"SELECT MAX(date) as last_date FROM {table} WHERE symbol = :symbol"
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), {"symbol": symbol})
                row = result.fetchone()
                if row and row[0]:
                    # Handle both string and datetime object returns
                    if isinstance(row[0], str):
                        return datetime.strptime(row[0], '%Y-%m-%d')
                    return row[0]
                return None
        except:
            return None

    # ==================== DATA SNAPSHOTS ====================

    def save_snapshot(self, df: pd.DataFrame):
        """Save latest snapshot."""
        if df.empty:
            return
            
        try:
            # Upsert logic for PostgreSQL
            # Using INSERT ... ON CONFLICT
            records = df.to_dict('records')
            
            # Map DataFrame columns to Table columns if needed, assuming direct mapping for now
            # But we need timestamp
            ts = datetime.now()
            for r in records:
                r['timestamp'] = ts
                
            query = """
                INSERT INTO latest_snapshot (
                    symbol, timestamp, ltp, change, change_percent, open, high, low, close, volume, 
                    value, prev_close, market_cap, sector, industry
                ) VALUES (
                    :symbol, :timestamp, :lastPrice, :change, :pChange, :open, :dayHigh, :dayLow, :closePrice, :totalTradedVolume, 
                    :totalTradedValue, :previousClose, :market_cap, :sector, :industry
                )
                ON CONFLICT (symbol) DO UPDATE SET
                    timestamp = excluded.timestamp,
                    ltp = excluded.ltp,
                    change = excluded.change,
                    change_percent = excluded.change_percent,
                    open = excluded.open,
                    high = excluded.high,
                    low = excluded.low,
                    close = excluded.close,
                    volume = excluded.volume,
                    value = excluded.value,
                    prev_close = excluded.prev_close
            """
            
            with self.engine.begin() as conn:
                 conn.execute(text(query), records)
                 
            logger.info(f"Saved snapshot for {len(df)} stocks")
        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")

    def get_latest_snapshot(self, symbol: str) -> Optional[Dict]:
        """Get latest snapshot for a symbol."""
        query = "SELECT * FROM latest_snapshot WHERE symbol = ?"
        # pd.read_sql_query handles the connection
        df = pd.read_sql_query(query, self.engine, params=(symbol,))
        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_all_snapshots(self) -> pd.DataFrame:
        """Get all latest snapshots."""
        query = "SELECT * FROM v_stock_overview ORDER BY symbol"
        return pd.read_sql_query(query, self.engine)
    
    # ==================== PRICE HISTORY ====================
    
    def save_price_history(self, df: pd.DataFrame):
        try:
            if df.empty: return
            
            # Efficient bulk insert using to_sql if possible, OR executemany
            # Here we use executemany with ON CONFLICT
            
            records = []
            for _, row in df.iterrows():
                records.append({
                    "symbol": row.get('symbol'),
                    "date": row.get('date'),
                    "open": row.get('open'),
                    "high": row.get('high'),
                    "low": row.get('low'),
                    "close": row.get('close'),
                    "volume": row.get('volume'),
                    "adj_close": row.get('adj_close', row.get('close'))
                })
                
            with self.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO price_history (symbol, date, open, high, low, close, volume, adj_close)
                    VALUES (:symbol, :date, :open, :high, :low, :close, :volume, :adj_close)
                    ON CONFLICT(symbol, date) DO UPDATE SET
                        open=excluded.open, high=excluded.high, low=excluded.low, close=excluded.close,
                        volume=excluded.volume, adj_close=excluded.adj_close
                """), records)
                
            logger.info(f"Saved {len(df)} price records")
        except Exception as e:
            logger.error(f"Error saving price history: {e}")

    def get_price_history(self, symbol: str, days: int = 365, start_date=None, end_date=None) -> pd.DataFrame:
        if start_date and end_date:
            query = """
                SELECT date, open, high, low, close, volume, adj_close
                FROM price_history
                WHERE symbol = ? AND date BETWEEN ? AND ?
                ORDER BY date ASC
            """
            df = pd.read_sql_query(query, self.engine, params=(symbol, start_date, end_date))
        else:
            query = """
                SELECT date, open, high, low, close, volume, adj_close
                FROM price_history
                WHERE symbol = ?
                ORDER BY date DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, self.engine, params=(symbol, days))
            df = df.sort_values('date')
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
        return df

    # ==================== FUNDAMENTALS (QUARTERLY) ====================
    
    def save_quarterly_results(self, df: pd.DataFrame):
        # Implementation skipped for brevity, similar to others...
        # Just logging error if called to prevent crash
        logger.warning("save_quarterly_results not fully refactored yet")
        pass

    def get_quarterly_results(self, symbol: str, limit: int = 4) -> pd.DataFrame:
        query = """
            SELECT * FROM quarterly_results 
            WHERE symbol = ?
            ORDER BY quarter DESC
            LIMIT ?
        """
        return pd.read_sql_query(query, self.engine, params=(symbol, limit))
    
    # ==================== ANNUAL RESULTS ====================
    
    def get_annual_results(self, symbol: str, limit: int = 5) -> pd.DataFrame:
        query = """
            SELECT * FROM annual_results 
            WHERE symbol = ?
            ORDER BY year DESC
            LIMIT ?
        """
        return pd.read_sql_query(query, self.engine, params=(symbol, limit))
    
    # ==================== BALANCE SHEET ====================
    
    def get_balance_sheet(self, symbol: str, limit: int = 5) -> pd.DataFrame:
         # Placeholder
         return pd.DataFrame()
    
    # ==================== COMPANY INFO ====================
    
    def save_company_info(self, data: Dict):
        # Placeholder
        pass
        
    def get_company_overview(self, symbol: str) -> Optional[Dict]:
        try:
            # 1. Get info
            info_query = "SELECT * FROM companies WHERE symbol = ?"
            info_df = pd.read_sql_query(info_query, self.engine, params=(symbol,))
            
            # 2. Get metrics from latest_snapshot
            metrics_query = "SELECT * FROM latest_snapshot WHERE symbol = ?"
            metrics_df = pd.read_sql_query(metrics_query, self.engine, params=(symbol,))
            
            if info_df.empty and metrics_df.empty:
                return None
                
            info = info_df.iloc[0].to_dict() if not info_df.empty else {}
            metrics = metrics_df.iloc[0].to_dict() if not metrics_df.empty else {}
            
            return {**info, **metrics}
        except Exception as e:
            logger.error(f"Error fetching overview: {e}")
            return None

    # ==================== SHAREHOLDING ====================
    
    def save_shareholding_pattern(self, df: pd.DataFrame):
        # Placeholder
        pass

    def get_shareholding_pattern(self, symbol: str, limit: int = 5) -> pd.DataFrame:
        query = """
            SELECT * FROM shareholding_pattern 
            WHERE symbol = ?
            ORDER BY quarter DESC
            LIMIT ?
        """
        return pd.read_sql_query(query, self.engine, params=(symbol, limit))
    
    # ==================== PEERS ====================
    
    def save_peers(self, df: pd.DataFrame):
        # Placeholder
        pass
        
    def get_peers(self, symbol: str) -> pd.DataFrame:
        """Get peer comparison."""
        query = "SELECT * FROM peers WHERE symbol = ? ORDER BY market_cap DESC"
        return pd.read_sql_query(query, self.engine, params=(symbol,))
    
    # ==================== LOGGING & UPDATES ====================
    
    def save_log(self, symbol, table_name, record_count, status, message, execution_time):
        """Save update log."""
        query = """
            INSERT INTO update_log (
                symbol, table_name, record_count, status, message, execution_time
            ) VALUES (:symbol, :table_name, :record_count, :status, :message, :execution_time)
        """
        try:
             with self.engine.begin() as conn:
                 conn.execute(text(query), {
                     "symbol": symbol, "table_name": table_name, "record_count": record_count,
                     "status": status, "message": message, "execution_time": execution_time
                 })
        except Exception as e:
            logger.error(f"Failed to save log: {e}")
    
    def get_last_update(self, symbol: str, table_name: str = None) -> Optional[datetime]:
        """Get last successful update time."""
        try:
            if table_name:
                query = """
                    SELECT MAX(created_at) as last_update
                    FROM update_log
                    WHERE symbol = :symbol AND table_name = :table_name AND status = 'success'
                """
                params = {"symbol": symbol, "table_name": table_name}
            else:
                query = """
                    SELECT MAX(created_at) as last_update
                    FROM update_log
                    WHERE symbol = :symbol AND status = 'success'
                """
                params = {"symbol": symbol}
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                row = result.fetchone()
                if row and row[0]:
                    if isinstance(row[0], str):
                         return datetime.fromisoformat(row[0])
                    return row[0]
            return None
        except Exception as e:
            logger.error(f"Error getting last update: {e}")
            return None
    
    def get_update_summary(self) -> pd.DataFrame:
        """Get update summary for all stocks."""
        query = """
            SELECT * FROM v_update_summary
            ORDER BY last_update DESC
        """
        return pd.read_sql_query(query, self.engine)
    
    def needs_update(self, symbol: str, hours: int = 24) -> bool:
        """Check if stock needs update."""
        last_update = self.get_last_update(symbol)
        if not last_update:
            return True
        
        age = datetime.now() - last_update
        return age > timedelta(hours=hours)
    
    # ==================== HELPER METHODS ====================
    
    def _parse_number(self, value) -> Optional[float]:
        """Parse number from string (handles ₹, %, commas)."""
        if value is None or pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        
        import re
        # Remove currency symbols, commas, spaces
        cleaned = re.sub(r'[₹,\s%]', '', str(value))
        try:
            return float(cleaned)
        except:
            return None
    
    def _parse_percentage(self, value) -> Optional[float]:
        """Parse percentage value."""
        if value is None or pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        
        # Remove % sign and convert
        cleaned = str(value).replace('%', '').strip()
        try:
            return float(cleaned)
        except:
            return None
    

    # ==================== INSTITUTIONAL & MARKET ====================

    def save_fii_dii_activity(self, data: Dict):
        """Save FII/DII activity."""
        if not data:
            return
            
        query = """
            INSERT INTO fii_dii_activity (
                date, fii_buy_value, fii_sell_value, fii_net_value,
                dii_buy_value, dii_sell_value, dii_net_value
            ) VALUES (:date, :fii_buy_value, :fii_sell_value, :fii_net_value, :dii_buy_value, :dii_sell_value, :dii_net_value)
            ON CONFLICT(date) DO UPDATE SET
                fii_buy_value = excluded.fii_buy_value,
                fii_sell_value = excluded.fii_sell_value,
                fii_net_value = excluded.fii_net_value,
                dii_buy_value = excluded.dii_buy_value,
                dii_sell_value = excluded.dii_sell_value,
                dii_net_value = excluded.dii_net_value
        """
        
        try:
            with self.engine.begin() as conn:
                conn.execute(text(query), data)
            logger.info(f"Saved FII/DII activity for {data.get('date')}")
        except Exception as e:
            logger.error(f"Error saving FII/DII activity: {e}")

    # ==================== CORPORATE ACTIONS ====================

    def save_corporate_actions(self, df: pd.DataFrame):
        """
        Save corporate actions to database.
        Expects NseUtils format: ['symbol', 'subject', 'exDate', 'recDate', ...]
        """
        try:
            if df.empty:
                return

            # Helper to parse date
            def parse_date(d):
                if not d or d == '-': return None
                try:
                    return datetime.strptime(d, '%d-%b-%Y').strftime('%Y-%m-%d')
                except:
                    return None

            records = []
            
            # Pre-fetch existing symbols
            with self.engine.connect() as conn:
                res = conn.execute(text("SELECT symbol FROM companies"))
                existing_symbols = set(row[0] for row in res)
            
            for _, row in df.iterrows():
                symbol = row.get('symbol')
                if not symbol or symbol not in existing_symbols: 
                    continue
                
                # Parse fields
                ex_date = parse_date(row.get('exDate'))
                record_date = parse_date(row.get('recDate'))
                subject = row.get('subject', '')
                
                # Simple classification
                action_type = 'other'
                if 'dividend' in subject.lower(): action_type = 'dividend'
                elif 'split' in subject.lower(): action_type = 'split'
                elif 'bonus' in subject.lower(): action_type = 'bonus'
                elif 'rights' in subject.lower(): action_type = 'rights'
                elif 'buyback' in subject.lower(): action_type = 'buyback'
                elif 'meeting' in subject.lower(): action_type = 'meeting'
                
                records.append({
                    "symbol": symbol, "ex_date": ex_date, "record_date": record_date,
                    "purpose": subject, "action_type": action_type
                })
                
            if not records: return
            
            with self.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO corporate_actions 
                    (symbol, ex_date, record_date, purpose, action_type)
                    VALUES (:symbol, :ex_date, :record_date, :purpose, :action_type)
                    ON CONFLICT DO NOTHING
                """), records)
                
            logger.info(f"Saved {len(records)} corporate actions.")
            
        except Exception as e:
            logger.error(f"Error saving corporate actions: {e}")

    # ==================== DERIVATIVES ====================

    def save_option_chain(self, df: pd.DataFrame):
        """
        Save option chain data.
        Expects NseUtils format (Wide format with CALLS_... and PUTS_...)
        """
        try:
            if df.empty:
                return

            # Need to transform Wide to Long
            timestamp = df.iloc[0].get('Fetch_Time')
            if timestamp:
                 try:
                    ts = datetime.strptime(timestamp, '%d-%b-%Y %H:%M:%S')
                 except:
                    ts = datetime.now()
            else:
                ts = datetime.now()
                
            symbol = df.iloc[0].get('Symbol')
            records = []
            
            for _, row in df.iterrows():
                expiry = row.get('Expiry_Date')
                strike = row.get('Strike_Price')
                
                # Parse Expiry
                try:
                    exp_date = datetime.strptime(expiry, '%d-%b-%Y').strftime('%Y-%m-%d')
                except:
                    continue

                # Common logic for CE and PE
                for type_ in ['CE', 'PE']:
                     prefix = "CALLS" if type_ == 'CE' else "PUTS"
                     if row.get(f'{prefix}_OI', 0) > 0 or row.get(f'{prefix}_LTP', 0) > 0:
                        records.append({
                            "symbol": symbol, "expiry_date": exp_date, "strike_price": strike,
                            "option_type": type_, "timestamp": ts,
                            "last_price": float(row.get(f'{prefix}_LTP', 0)),
                            "open_interest": int(row.get(f'{prefix}_OI', 0)),
                            "oi_change": int(row.get(f'{prefix}_Chng_in_OI', 0)),
                            "volume": int(row.get(f'{prefix}_Volume', 0)),
                            "iv": float(row.get(f'{prefix}_IV', 0)),
                            "delta": float(row.get(f'{prefix}_Delta', 0)),
                            "gamma": float(row.get(f'{prefix}_Gamma', 0)),
                            "theta": float(row.get(f'{prefix}_Theta', 0)),
                            "vega": float(row.get(f'{prefix}_Vega', 0))
                        })
            
            if not records: return

            with self.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO option_chain 
                    (symbol, expiry_date, strike_price, option_type, timestamp, last_price, open_interest, oi_change, volume, iv, delta, gamma, theta, vega)
                    VALUES (:symbol, :expiry_date, :strike_price, :option_type, :timestamp, :last_price, :open_interest, :oi_change, :volume, :iv, :delta, :gamma, :theta, :vega)
                    ON CONFLICT(symbol, expiry_date, strike_price, option_type, timestamp) DO UPDATE SET
                    last_price=excluded.last_price, open_interest=excluded.open_interest,
                    oi_change=excluded.oi_change, volume=excluded.volume, iv=excluded.iv,
                    delta=excluded.delta, gamma=excluded.gamma, theta=excluded.theta, vega=excluded.vega
                """), records)
            
            logger.info(f"Saved {len(records)} option chain records for {symbol}")
            
        except Exception as e:
            logger.error(f"Error saving option chain: {e}")

    def get_latest_option_chain(self, symbol: str) -> List[Dict]:
        """
        Get the most recent option chain data for a symbol.
        """
        try:
            # First find the latest timestamp
            query_ts = "SELECT MAX(timestamp) as last_ts FROM option_chain WHERE symbol = ?"
            res = pd.read_sql_query(query_ts, self.engine, params=(symbol.upper(),))
            if res.empty or res.iloc[0]['last_ts'] is None:
                return []
            
            last_ts = res.iloc[0]['last_ts']
            
            # Fetch all records for that timestamp
            query = "SELECT * FROM option_chain WHERE symbol = ? AND timestamp = ?"
            df = pd.read_sql_query(query, self.engine, params=(symbol.upper(), last_ts))
            return df.to_dict(orient='records')
        except Exception as e:
            logger.error(f"Error fetching latest option chain: {e}")
            return []

    def save_market_breadth(self, data: Dict):
        """Save market breadth."""
        if not data:
            return
            
        query = """
            INSERT INTO market_breadth (
                date, advances, declines, unchanged, advance_decline_ratio
            ) VALUES (:date, :advances, :declines, :unchanged, :ratio)
            ON CONFLICT(date) DO UPDATE SET
                advances = excluded.advances,
                declines = excluded.declines,
                unchanged = excluded.unchanged,
                advance_decline_ratio = excluded.advance_decline_ratio
        """
        
        try:
            with self.engine.begin() as conn:
                conn.execute(text(query), data)
            logger.info(f"Saved market breadth for {data.get('date')}")
        except Exception as e:
            logger.error(f"Error saving market breadth: {e}")
    
    # ==================== TECHNICALS ====================

    def save_technical_indicators(self, symbol: str, records: List[Dict]):
        """Save technical indicators."""
        if not records:
            return
            
        try:
            # Ensure symbol is in every record
            for r in records: r['symbol'] = symbol
                
            with self.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO technical_indicators 
                    (symbol, date, sma_20, sma_50, sma_200, rsi, macd, macd_signal, adx)
                    VALUES (:symbol, :date, :sma_20, :sma_50, :sma_200, :rsi, :macd, :macd_signal, :adx)
                    ON CONFLICT(symbol, date) DO UPDATE SET
                    sma_20=excluded.sma_20, sma_50=excluded.sma_50, sma_200=excluded.sma_200,
                    rsi=excluded.rsi, macd=excluded.macd, macd_signal=excluded.macd_signal, adx=excluded.adx
                """), records)
            
            logger.info(f"Saved {len(records)} technical indicators for {symbol}")
            
        except Exception as e:
            logger.error(f"Error saving technicals: {e}")

    # ==================== UTILITY METHODS ====================
    
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """Get table schema information."""
        # Postgres specific
        query = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = ?"
        return pd.read_sql_query(query, self.engine, params=(table_name,))
    
    def get_row_count(self, table_name: str) -> int:
        """Get row count for a table."""
        # Using execute returns list in my new implementation if it's SELECT
        rows = self.execute(f"SELECT COUNT(*) as count FROM {table_name}", fetch_all=True)
        return rows[0][0]
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        # Size in PG
        try:
            size_rows = self.execute("SELECT pg_database_size(current_database())", fetch_all=True)
            size_mb = size_rows[0][0] / (1024 * 1024)
        except:
            size_mb = 0
            
        stats = {
            'database_size': size_mb,
            'table_counts': {}
        }
        
        for table in ALL_TABLES:
            try:
                stats['table_counts'][table] = self.get_row_count(table)
            except:
                stats['table_counts'][table] = 0
        
        return stats
    
    def vacuum(self):
        """Optimize database (reclaim space)."""
        logger.info("Running VACUUM to optimize database...")
        try:
            with self.engine.connect() as conn:
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(text("VACUUM"))
            logger.info("✅ Database optimized")
        except Exception as e:
            logger.error(f"VACUUM failed: {e}")
    
    def _save_deals_generic(self, df, table):
        try:
            if df is None or df.empty: return
            records = []
            for _, row in df.iterrows():
                 records.append({
                     "symbol": row.get('symbol'), "deal_date": row.get('date'), 
                     "client_name": row.get('clientName'), "deal_type": row.get('transactionType'),
                     "quantity": int(self._parse_number(row.get('quantityTraded', 0)) or 0),
                     "price": float(self._parse_number(row.get('tradePrice', 0)) or 0),
                     "value": float(self._parse_number(row.get('quantityTraded', 0) or 0)) * float(self._parse_number(row.get('tradePrice', 0)) or 0)
                 })
            
            with self.engine.begin() as conn:
                conn.execute(text(f"""
                    INSERT INTO {table} (symbol, deal_date, client_name, deal_type, quantity, price, value)
                    VALUES (:symbol, :deal_date, :client_name, :deal_type, :quantity, :price, :value)
                    ON CONFLICT DO NOTHING
                """), records)
        except Exception as e:
             logger.error(f"Error saving {table}: {e}")

    def save_bulk_deals(self, df: pd.DataFrame):
        self._save_deals_generic(df, "bulk_deals")

    def save_block_deals(self, df: pd.DataFrame):
        self._save_deals_generic(df, "block_deals")

    def save_insider_trading(self, df: pd.DataFrame):
        try:
            if df is None or df.empty: return
            records = []
            for _, row in df.iterrows():
                records.append({
                    "symbol": row.get('symbol'), "person_name": row.get('acquirerName'), "person_category": row.get('category'),
                    "securities_type": row.get('secType'), "transaction_type": row.get('tdpAdvisers'),
                    "number_of_securities": int(self._parse_number(row.get('noOfSecurities', 0)) or 0),
                    "value": float(self._parse_number(row.get('valueInRs', 0)) or 0),
                    "acquisition_date": row.get('acqFromDate')
                })
            with self.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO insider_trading (symbol, person_name, person_category, securities_type, transaction_type, number_of_securities, value, acquisition_date)
                    VALUES (:symbol, :person_name, :person_category, :securities_type, :transaction_type, :number_of_securities, :value, :acquisition_date)
                    ON CONFLICT DO NOTHING
                """), records)
        except Exception as e:
            logger.error(f"Error saving insider: {e}")

    def save_futures_data(self, df: pd.DataFrame):
        try:
            if df is None or df.empty: return
            records = []
            ts = datetime.now()
            for _, row in df.iterrows():
                records.append({
                    "symbol": row.get('symbol'), "expiry_date": row.get('expiryDate'), "timestamp": ts,
                    "underlying_value": float(row.get('underlyingValue', 0)), "futures_price": float(row.get('lastPrice', 0)),
                    "open_interest": int(row.get('openInterest', 0)), "oi_change": int(row.get('changeinOpenInterest', 0)),
                    "volume": int(row.get('totalTradedVolume', 0)), "basis": float(row.get('lastPrice', 0)) - float(row.get('underlyingValue', 0))
                })
            with self.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO futures_data (symbol, expiry_date, timestamp, underlying_value, futures_price, open_interest, oi_change, volume, basis)
                    VALUES (:symbol, :expiry_date, :timestamp, :underlying_value, :futures_price, :open_interest, :oi_change, :volume, :basis)
                    ON CONFLICT(symbol, expiry_date, timestamp) DO UPDATE SET 
                    futures_price=excluded.futures_price, open_interest=excluded.open_interest, 
                    oi_change=excluded.oi_change, volume=excluded.volume, basis=excluded.basis
                """), records)
        except Exception as e:
            logger.error(f"Error saving futures: {e}")

    def save_execution(self, execution_data: Dict[str, Any]):
        """Save order execution audit log."""
        
        ex_data = execution_data.copy()
        # Serialize JSON fields
        ex_data['raw_payload'] = json.dumps(ex_data.get('raw_payload')) if ex_data.get('raw_payload') else None
        ex_data['raw_response'] = json.dumps(ex_data.get('raw_response')) if ex_data.get('raw_response') else None
        ex_data['metadata'] = json.dumps(ex_data.get('metadata')) if ex_data.get('metadata') else None
        ex_data['created_at'] = datetime.now()
        
        # Ensure all keys exist
        defaults = {
            'symbol': None, 'order_type': None, 'quantity': 0, 'price': 0.0,
            'execution_mode': 'PAPER', 'execution_status': 'UNKNOWN',
            'execution_block_reason': None, 'feed_state': 'UNKNOWN',
            'ltp_source': None, 'ltp_age_ms': 0, 'order_id': None,
            'decision_id': None, 'drift_bps': 0.0
        }
        for k, v in defaults.items():
            if k not in ex_data: ex_data[k] = v

        query = """
            INSERT INTO order_executions (
                symbol, order_type, quantity, price, execution_mode,
                execution_status, execution_block_reason, feed_state, 
                ltp_source, ltp_age_ms, order_id, decision_id,
                drift_bps, raw_payload, raw_response, created_at
            ) VALUES (
                :symbol, :order_type, :quantity, :price, :execution_mode,
                :execution_status, :execution_block_reason, :feed_state, 
                :ltp_source, :ltp_age_ms, :order_id, :decision_id,
                :drift_bps, :raw_payload, :raw_response, :created_at
            )
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(text(query), ex_data)
            logger.info(f"Saved execution audit for {execution_data.get('symbol')}")
        except Exception as e:
            logger.error(f"Error saving execution audit: {e}")

    def save_alert(self, alert_data: Dict[str, Any]):
        """Save a system alert to the database."""
        query = """
            INSERT INTO alerts (
                alert_type, level, symbol, message, metadata
            ) VALUES (:type, :level, :symbol, :message, :metadata)
        """
        try:
            data = {
                "type": alert_data.get('type'),
                "level": alert_data.get('level'),
                "symbol": alert_data.get('symbol'),
                "message": alert_data.get('message'),
                "metadata": json.dumps(alert_data.get('metadata')) if alert_data.get('metadata') else None
            }
            with self.engine.begin() as conn:
                conn.execute(text(query), data)
            logger.info(f"Saved alert: {alert_data.get('type')} - {alert_data.get('message')}")
        except Exception as e:
            logger.error(f"Error saving alert: {e}")

    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Fetch latest alerts from the database."""
        try:
            rows = self.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT :limit", {"limit": limit}, fetch_all=True)
            # Fetchall returns list of Row objects, which act like named tuples.
            # We need to dict them.
            return [dict(row._mapping) for row in rows]
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []

    def get_last_execution(self) -> Optional[Dict]:
        """Get the most recent execution record."""
        try:
            rows = self.execute("SELECT * FROM order_executions ORDER BY created_at DESC LIMIT 1", fetch_all=True)
            if rows:
                return dict(rows[0]._mapping)
            return None
        except Exception as e:
            logger.error(f"Error getting last execution: {e}")
            return None

    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")