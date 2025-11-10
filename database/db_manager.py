"""
SQLite Database Manager - Hybrid Schema
Handles both denormalized tables and EAV custom metrics
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta
import logging
import json

from .schema import CREATE_TABLES, ALL_TABLES

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage SQLite database operations with hybrid schema."""
    
    def __init__(self, db_path: str = 'stock_data.db'):
        self.db_path = Path(db_path)
        self.conn = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database and create tables."""
        self.conn = sqlite3.connect(
            self.db_path, 
            check_same_thread=False,
            timeout=30.0
        )
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Create all tables
        self.conn.executescript(CREATE_TABLES)
        self.conn.commit()
        
        logger.info(f"✅ Database initialized at {self.db_path}")
        
        # Verify tables
        self._verify_schema()
    
    def _verify_schema(self):
        """Verify all tables were created."""
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing = set(ALL_TABLES) - set(existing_tables)
        if missing:
            logger.warning(f"Missing tables: {missing}")
        else:
            logger.info(f"✅ All {len(ALL_TABLES)} tables verified")
    
    def execute(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """Execute a SQL query."""
        try:
            if params:
                return self.conn.execute(query, params)
            return self.conn.execute(query)
        except sqlite3.Error as e:
            logger.error(f"SQL error: {e}\nQuery: {query}")
            raise
    
    def executemany(self, query: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """Execute a SQL query with multiple parameter sets."""
        try:
            return self.conn.executemany(query, params_list)
        except sqlite3.Error as e:
            logger.error(f"SQL error: {e}\nQuery: {query}")
            raise
    
    def commit(self):
        """Commit changes."""
        self.conn.commit()
    
    def rollback(self):
        """Rollback changes."""
        self.conn.rollback()
    
    def begin_transaction(self):
        """Begin a transaction."""
        self.conn.execute("BEGIN TRANSACTION")
    
    # ==================== COMPANY OPERATIONS ====================
    
    def add_company(
        self, 
        symbol: str, 
        company_name: str = None, 
        sector: str = None,
        industry: str = None,
        isin: str = None,
        listing_date: str = None
    ):
        """Add or update company in master table."""
        query = """
            INSERT INTO companies (symbol, company_name, sector, industry, isin, listing_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                company_name = COALESCE(excluded.company_name, company_name),
                sector = COALESCE(excluded.sector, sector),
                industry = COALESCE(excluded.industry, industry),
                isin = COALESCE(excluded.isin, isin),
                listing_date = COALESCE(excluded.listing_date, listing_date),
                updated_at = CURRENT_TIMESTAMP
        """
        self.execute(query, (symbol, company_name, sector, industry, isin, listing_date))
        self.commit()
        logger.debug(f"Added/updated company: {symbol}")
    
    def get_company(self, symbol: str) -> Optional[Dict]:
        """Get company information."""
        query = "SELECT * FROM companies WHERE symbol = ?"
        cursor = self.execute(query, (symbol,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_companies(self, sector: str = None) -> List[Dict]:
        """Get all companies, optionally filtered by sector."""
        if sector:
            query = "SELECT * FROM companies WHERE sector = ? ORDER BY symbol"
            cursor = self.execute(query, (sector,))
        else:
            query = "SELECT * FROM companies ORDER BY symbol"
            cursor = self.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_sectors(self) -> List[str]:
        """Get list of unique sectors."""
        query = "SELECT DISTINCT sector FROM companies WHERE sector IS NOT NULL ORDER BY sector"
        cursor = self.execute(query)
        return [row[0] for row in cursor.fetchall()]
    
    # ==================== LATEST SNAPSHOT ====================
    
    def update_snapshot(self, symbol: str, data: Dict):
        """Update latest snapshot for a company."""
        query = """
            INSERT INTO latest_snapshot (
                symbol, current_price, change, change_percent, market_cap,
                pe_ratio, pb_ratio, roe, roce, dividend_yield, eps,
                book_value, face_value, high_52w, low_52w, volume
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                current_price = excluded.current_price,
                change = excluded.change,
                change_percent = excluded.change_percent,
                market_cap = excluded.market_cap,
                pe_ratio = excluded.pe_ratio,
                pb_ratio = excluded.pb_ratio,
                roe = excluded.roe,
                roce = excluded.roce,
                dividend_yield = excluded.dividend_yield,
                eps = excluded.eps,
                book_value = excluded.book_value,
                face_value = excluded.face_value,
                high_52w = excluded.high_52w,
                low_52w = excluded.low_52w,
                volume = excluded.volume,
                snapshot_date = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
        """
        
        self.execute(query, (
            symbol,
            data.get('current_price'),
            data.get('change'),
            data.get('change_percent'),
            data.get('market_cap'),
            data.get('pe_ratio'),
            data.get('pb_ratio'),
            data.get('roe'),
            data.get('roce'),
            data.get('dividend_yield'),
            data.get('eps'),
            data.get('book_value'),
            data.get('face_value'),
            data.get('high_52w'),
            data.get('low_52w'),
            data.get('volume')
        ))
        self.commit()
        logger.debug(f"Updated snapshot for {symbol}")
    
    def get_snapshot(self, symbol: str) -> Optional[Dict]:
        """Get latest snapshot for a symbol."""
        query = "SELECT * FROM latest_snapshot WHERE symbol = ?"
        cursor = self.execute(query, (symbol,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_snapshots(self) -> pd.DataFrame:
        """Get all latest snapshots."""
        query = "SELECT * FROM v_stock_overview ORDER BY symbol"
        return pd.read_sql_query(query, self.conn)
    
    # ==================== PRICE HISTORY ====================
    
    def save_price_history(self, symbol: str, df: pd.DataFrame):
        """Save historical OHLCV data."""
        if df is None or df.empty:
            logger.warning(f"No price history to save for {symbol}")
            return
        
        # Prepare data
        df = df.copy()
        
        # Handle index - convert to column if needed
        if df.index.name in ['Date', 'date', 'timestamp']:
            df = df.reset_index()
        elif 'Date' not in df.columns and 'date' not in df.columns:
            # If no date column and index is datetime, use it
            if isinstance(df.index, pd.DatetimeIndex):
                df['date'] = df.index
                df = df.reset_index(drop=True)
        
        # Standardize column names (case-insensitive)
        df.columns = df.columns.str.lower()
        
        # Ensure we have a date column
        if 'date' not in df.columns:
            logger.error(f"No date column found in price history for {symbol}")
            logger.error(f"Available columns: {df.columns.tolist()}")
            return
        
        # Convert date to string format YYYY-MM-DD
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        # Remove any rows with null dates
        df = df.dropna(subset=['date'])
        
        if df.empty:
            logger.warning(f"No valid dates in price history for {symbol}")
            return
        
        # Insert or update
        query = """
            INSERT INTO price_history (symbol, date, open, high, low, close, volume, adj_close)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, date) DO UPDATE SET
                open = excluded.open,
                high = excluded.high,
                low = excluded.low,
                close = excluded.close,
                volume = excluded.volume,
                adj_close = excluded.adj_close
        """
        
        data_tuples = []
        for _, row in df.iterrows():
            # Skip rows with invalid dates
            if pd.isna(row.get('date')) or not row.get('date'):
                continue
                
            data_tuples.append((
                symbol,
                row.get('date'),
                self._parse_number(row.get('open')),
                self._parse_number(row.get('high')),
                self._parse_number(row.get('low')),
                self._parse_number(row.get('close')),
                int(row.get('volume', 0)) if row.get('volume') else None,
                self._parse_number(row.get('adj_close') or row.get('adj close'))
            ))
        
        if not data_tuples:
            logger.warning(f"No valid price records to save for {symbol}")
            return
        
        try:
            self.executemany(query, data_tuples)
            self.commit()
            logger.info(f"Saved {len(data_tuples)} price records for {symbol}")
        except Exception as e:
            logger.error(f"Error saving price history: {e}")
            logger.error(f"Sample data: {data_tuples[0] if data_tuples else 'None'}")
            raise
    
    def get_price_history(
        self, 
        symbol: str, 
        days: int = 365,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """Get historical prices."""
        if start_date and end_date:
            query = """
                SELECT date, open, high, low, close, volume, adj_close
                FROM price_history
                WHERE symbol = ? AND date BETWEEN ? AND ?
                ORDER BY date ASC
            """
            df = pd.read_sql_query(query, self.conn, params=(symbol, start_date, end_date))
        else:
            query = """
                SELECT date, open, high, low, close, volume, adj_close
                FROM price_history
                WHERE symbol = ?
                ORDER BY date DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, self.conn, params=(symbol, days))
            df = df.sort_values('date')
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        return df
    
    def get_latest_price_date(self, symbol: str) -> Optional[datetime]:
        """Get the date of the latest price record."""
        query = "SELECT MAX(date) as latest FROM price_history WHERE symbol = ?"
        cursor = self.execute(query, (symbol,))
        row = cursor.fetchone()
        if row and row['latest']:
            return datetime.strptime(row['latest'], '%Y-%m-%d')
        return None
    
    # ==================== QUARTERLY RESULTS ====================
    
    def save_quarterly_results(self, symbol: str, df: pd.DataFrame):
        """Save quarterly results."""
        if df is None or df.empty:
            logger.warning(f"No quarterly results to save for {symbol}")
            return
        
        # Parse the DataFrame (first column is metric name, rest are quarters)
        if df.shape[1] < 2:
            logger.warning("Quarterly results DataFrame has insufficient columns")
            return
        
        quarters = df.columns[1:]  # Skip first column (metric names)
        
        for quarter in quarters:
            try:
                # Extract metrics
                metrics = {}
                for idx, row in df.iterrows():
                    metric_name = str(row.iloc[0]).strip()
                    value = row[quarter]
                    
                    # Map to database columns
                    if 'Sales' in metric_name:
                        metrics['sales'] = self._parse_number(value)
                    elif 'Expenses' in metric_name:
                        metrics['expenses'] = self._parse_number(value)
                    elif 'Operating Profit' == metric_name:
                        metrics['operating_profit'] = self._parse_number(value)
                    elif 'OPM %' == metric_name:
                        metrics['opm_percent'] = self._parse_number(value)
                    elif 'Other Income' in metric_name:
                        metrics['other_income'] = self._parse_number(value)
                    elif 'Interest' == metric_name:
                        metrics['interest'] = self._parse_number(value)
                    elif 'Depreciation' == metric_name:
                        metrics['depreciation'] = self._parse_number(value)
                    elif 'Profit before tax' in metric_name:
                        metrics['profit_before_tax'] = self._parse_number(value)
                    elif 'Tax %' == metric_name:
                        metrics['tax_percent'] = self._parse_number(value)
                    elif 'Net Profit' in metric_name:
                        metrics['net_profit'] = self._parse_number(value)
                    elif 'EPS' in metric_name:
                        metrics['eps'] = self._parse_number(value)
                
                query = """
                    INSERT INTO quarterly_results (
                        symbol, quarter, sales, expenses, operating_profit, opm_percent,
                        other_income, interest, depreciation, profit_before_tax,
                        tax_percent, net_profit, eps
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(symbol, quarter) DO UPDATE SET
                        sales = excluded.sales,
                        expenses = excluded.expenses,
                        operating_profit = excluded.operating_profit,
                        opm_percent = excluded.opm_percent,
                        other_income = excluded.other_income,
                        interest = excluded.interest,
                        depreciation = excluded.depreciation,
                        profit_before_tax = excluded.profit_before_tax,
                        tax_percent = excluded.tax_percent,
                        net_profit = excluded.net_profit,
                        eps = excluded.eps,
                        updated_at = CURRENT_TIMESTAMP
                """
                
                self.execute(query, (
                    symbol, quarter,
                    metrics.get('sales'),
                    metrics.get('expenses'),
                    metrics.get('operating_profit'),
                    metrics.get('opm_percent'),
                    metrics.get('other_income'),
                    metrics.get('interest'),
                    metrics.get('depreciation'),
                    metrics.get('profit_before_tax'),
                    metrics.get('tax_percent'),
                    metrics.get('net_profit'),
                    metrics.get('eps')
                ))
            except Exception as e:
                logger.error(f"Error saving quarterly data for {quarter}: {e}")
        
        self.commit()
        logger.info(f"Saved quarterly results for {symbol}")
    
    def get_quarterly_results(self, symbol: str, limit: int = 12) -> pd.DataFrame:
        """Get quarterly results."""
        query = """
            SELECT * FROM quarterly_results
            WHERE symbol = ?
            ORDER BY quarter DESC
            LIMIT ?
        """
        return pd.read_sql_query(query, self.conn, params=(symbol, limit))
    
    # ==================== ANNUAL RESULTS ====================
    
    def save_annual_results(self, symbol: str, df: pd.DataFrame):
        """Save annual profit & loss results."""
        if df is None or df.empty:
            logger.warning(f"No annual results to save for {symbol}")
            return
        
        years = df.columns[1:]  # Skip first column
        
        for year in years:
            try:
                metrics = {}
                for idx, row in df.iterrows():
                    metric_name = str(row.iloc[0]).strip()
                    value = row[year]
                    
                    if 'Sales' in metric_name:
                        metrics['sales'] = self._parse_number(value)
                    elif 'Expenses' in metric_name:
                        metrics['expenses'] = self._parse_number(value)
                    elif 'Operating Profit' == metric_name:
                        metrics['operating_profit'] = self._parse_number(value)
                    elif 'OPM %' == metric_name:
                        metrics['opm_percent'] = self._parse_number(value)
                    elif 'Other Income' in metric_name:
                        metrics['other_income'] = self._parse_number(value)
                    elif 'Interest' == metric_name:
                        metrics['interest'] = self._parse_number(value)
                    elif 'Depreciation' == metric_name:
                        metrics['depreciation'] = self._parse_number(value)
                    elif 'Profit before tax' in metric_name:
                        metrics['profit_before_tax'] = self._parse_number(value)
                    elif 'Tax %' == metric_name:
                        metrics['tax_percent'] = self._parse_number(value)
                    elif 'Net Profit' in metric_name:
                        metrics['net_profit'] = self._parse_number(value)
                    elif 'EPS' in metric_name:
                        metrics['eps'] = self._parse_number(value)
                    elif 'Dividend' in metric_name:
                        metrics['dividend_payout'] = self._parse_number(value)
                
                query = """
                    INSERT INTO annual_results (
                        symbol, year, sales, expenses, operating_profit, opm_percent,
                        other_income, interest, depreciation, profit_before_tax,
                        tax_percent, net_profit, eps, dividend_payout
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(symbol, year) DO UPDATE SET
                        sales = excluded.sales,
                        expenses = excluded.expenses,
                        operating_profit = excluded.operating_profit,
                        opm_percent = excluded.opm_percent,
                        other_income = excluded.other_income,
                        interest = excluded.interest,
                        depreciation = excluded.depreciation,
                        profit_before_tax = excluded.profit_before_tax,
                        tax_percent = excluded.tax_percent,
                        net_profit = excluded.net_profit,
                        eps = excluded.eps,
                        dividend_payout = excluded.dividend_payout,
                        updated_at = CURRENT_TIMESTAMP
                """
                
                self.execute(query, (
                    symbol, year,
                    metrics.get('sales'),
                    metrics.get('expenses'),
                    metrics.get('operating_profit'),
                    metrics.get('opm_percent'),
                    metrics.get('other_income'),
                    metrics.get('interest'),
                    metrics.get('depreciation'),
                    metrics.get('profit_before_tax'),
                    metrics.get('tax_percent'),
                    metrics.get('net_profit'),
                    metrics.get('eps'),
                    metrics.get('dividend_payout')
                ))
            except Exception as e:
                logger.error(f"Error saving annual data for {year}: {e}")
        
        self.commit()
        logger.info(f"Saved annual results for {symbol}")
    
    def get_annual_results(self, symbol: str, limit: int = 10) -> pd.DataFrame:
        """Get annual results."""
        query = """
            SELECT * FROM annual_results
            WHERE symbol = ?
            ORDER BY year DESC
            LIMIT ?
        """
        return pd.read_sql_query(query, self.conn, params=(symbol, limit))
    
    # ==================== SHAREHOLDING ====================
    
    def save_shareholding(self, symbol: str, df: pd.DataFrame):
        """Save shareholding pattern."""
        if df is None or df.empty:
            logger.warning(f"No shareholding data to save for {symbol}")
            return
        
        quarters = df.columns[1:]  # Skip first column
        
        for quarter in quarters:
            try:
                shareholding = {}
                for idx, row in df.iterrows():
                    holder_type = str(row.iloc[0]).strip()
                    value = self._parse_percentage(row[quarter])
                    
                    if 'Promoter' in holder_type:
                        shareholding['promoters'] = value
                    elif 'FII' in holder_type:
                        shareholding['fii'] = value
                    elif 'DII' in holder_type:
                        shareholding['dii'] = value
                    elif 'Public' in holder_type:
                        shareholding['public'] = value
                    elif 'Government' in holder_type:
                        shareholding['government'] = value
                
                query = """
                    INSERT INTO shareholding (symbol, quarter, promoters, fii, dii, public, government)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(symbol, quarter) DO UPDATE SET
                        promoters = excluded.promoters,
                        fii = excluded.fii,
                        dii = excluded.dii,
                        public = excluded.public,
                        government = excluded.government,
                        updated_at = CURRENT_TIMESTAMP
                """
                
                self.execute(query, (
                    symbol, quarter,
                    shareholding.get('promoters'),
                    shareholding.get('fii'),
                    shareholding.get('dii'),
                    shareholding.get('public'),
                    shareholding.get('government')
                ))
            except Exception as e:
                logger.error(f"Error saving shareholding for {quarter}: {e}")
        
        self.commit()
        logger.info(f"Saved shareholding pattern for {symbol}")
    
    def get_shareholding(self, symbol: str, limit: int = 8) -> pd.DataFrame:
        """Get shareholding pattern."""
        query = """
            SELECT * FROM shareholding
            WHERE symbol = ?
            ORDER BY quarter DESC
            LIMIT ?
        """
        return pd.read_sql_query(query, self.conn, params=(symbol, limit))
    
    # ==================== PEERS ====================
    
    def save_peers(self, symbol: str, df: pd.DataFrame):
        """Save peer comparison."""
        if df is None or df.empty:
            logger.warning(f"No peer data to save for {symbol}")
            return
        
        # Delete existing peers
        self.execute("DELETE FROM peers WHERE symbol = ?", (symbol,))
        
        query = """
            INSERT INTO peers (
                symbol, peer_symbol, peer_name, cmp, pe, market_cap,
                div_yield, np_qtr, qtr_profit_var, sales_qtr, qtr_sales_var, roce, roe
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        for _, row in df.iterrows():
            peer_name = row.get('Name', '')
            if peer_name and 'Median' not in peer_name:
                self.execute(query, (
                    symbol,
                    peer_name,
                    peer_name,
                    self._parse_number(row.get('CMP  Rs.')),
                    self._parse_number(row.get('P/E')),
                    self._parse_number(row.get('Mar Cap  Rs.Cr.')),
                    self._parse_number(row.get('Div Yld  %')),
                    self._parse_number(row.get('NP Qtr  Rs.Cr.')),
                    self._parse_number(row.get('Qtr Profit Var  %')),
                    self._parse_number(row.get('Sales Qtr  Rs.Cr.')),
                    self._parse_number(row.get('Qtr Sales Var  %')),
                    self._parse_number(row.get('ROCE  %')),
                    self._parse_number(row.get('ROE  %'))
                ))
        
        self.commit()
        logger.info(f"Saved {len(df)} peers for {symbol}")
    
    def get_peers(self, symbol: str) -> pd.DataFrame:
        """Get peer comparison."""
        query = "SELECT * FROM peers WHERE symbol = ? ORDER BY market_cap DESC"
        return pd.read_sql_query(query, self.conn, params=(symbol,))
    
    # ==================== CUSTOM METRICS (EAV) ====================
    
    def save_custom_metric(
        self,
        symbol: str,
        metric_name: str,
        metric_value: Any,
        metric_type: str = 'text',
        period: str = None,
        category: str = 'custom'
    ):
        """Save a custom metric (flexible EAV pattern)."""
        query = """
            INSERT INTO custom_metrics (
                symbol, metric_name, metric_value, metric_type, period, category
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        self.execute(query, (
            symbol, metric_name, str(metric_value), metric_type, period, category
        ))
        self.commit()
    
    def get_custom_metrics(
        self,
        symbol: str,
        category: str = None,
        period: str = None
    ) -> List[Dict]:
        """Get custom metrics."""
        if category and period:
            query = """
                SELECT * FROM custom_metrics
                WHERE symbol = ? AND category = ? AND period = ?
                ORDER BY created_at DESC
            """
            cursor = self.execute(query, (symbol, category, period))
        elif category:
            query = """
                SELECT * FROM custom_metrics
                WHERE symbol = ? AND category = ?
                ORDER BY created_at DESC
            """
            cursor = self.execute(query, (symbol, category))
        else:
            query = """
                SELECT * FROM custom_metrics
                WHERE symbol = ?
                ORDER BY created_at DESC
            """
            cursor = self.execute(query, (symbol,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # ==================== UPDATE LOG ====================
    
    def log_update(
        self,
        symbol: str,
        table_name: str,
        record_count: int = 0,
        status: str = 'success',
        message: str = None,
        execution_time: float = None
    ):
        """Log a data update."""
        query = """
            INSERT INTO update_log (
                symbol, table_name, record_count, status, message, execution_time
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        self.execute(query, (symbol, table_name, record_count, status, message, execution_time))
        self.commit()
    
    def get_last_update(self, symbol: str, table_name: str = None) -> Optional[datetime]:
        """Get last successful update time."""
        if table_name:
            query = """
                SELECT MAX(created_at) as last_update
                FROM update_log
                WHERE symbol = ? AND table_name = ? AND status = 'success'
            """
            cursor = self.execute(query, (symbol, table_name))
        else:
            query = """
                SELECT MAX(created_at) as last_update
                FROM update_log
                WHERE symbol = ? AND status = 'success'
            """
            cursor = self.execute(query, (symbol,))
        
        row = cursor.fetchone()
        if row and row['last_update']:
            return datetime.fromisoformat(row['last_update'])
        return None
    
    def get_update_summary(self) -> pd.DataFrame:
        """Get update summary for all stocks."""
        query = """
            SELECT * FROM v_update_summary
            ORDER BY last_update DESC
        """
        return pd.read_sql_query(query, self.conn)
    
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
    
    # ==================== UTILITY METHODS ====================
    
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """Get table schema information."""
        query = f"PRAGMA table_info({table_name})"
        return pd.read_sql_query(query, self.conn)
    
    def get_row_count(self, table_name: str) -> int:
        """Get row count for a table."""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        cursor = self.execute(query)
        return cursor.fetchone()['count']
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        stats = {
            'database_size': self.db_path.stat().st_size / (1024 * 1024),  # MB
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
        self.conn.execute("VACUUM")
        logger.info("✅ Database optimized")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")