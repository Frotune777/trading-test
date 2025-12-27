"""
Corporate Events Data Collection Service
Fetches and stores corporate events (dividends, splits, bonuses, rights) from NSE
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from app.data_sources.nse_utils import NseUtils

logger = logging.getLogger(__name__)


class CorporateEventsService:
    """
    Service to fetch and store NSE corporate events data
    """
    
    def __init__(self, db_path: str = 'stock_data.db'):
        self.db_path = db_path
        self.nse_utils = NseUtils()
    
    def fetch_and_store(self, days: int = 90, event_filter: str = None) -> Dict[str, Any]:
        """
        Fetch corporate events for the last N days and store in database
        
        Args:
            days: Number of days to fetch (default: 90)
            event_filter: Optional filter (e.g., 'Dividend', 'Bonus', 'Split')
            
        Returns:
            Dict with fetch results
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            logger.info(f"Fetching corporate events from {start_date.date()} to {end_date.date()}")
            
            # Fetch from NSE
            df = self.nse_utils.get_corporate_action(
                from_date_str=start_date.strftime('%d-%m-%Y'),
                to_date_str=end_date.strftime('%d-%m-%Y'),
                filter=event_filter
            )
            
            if df is None or df.empty:
                logger.warning("No corporate events data returned from NSE")
                return {
                    'status': 'no_data',
                    'records_fetched': 0,
                    'records_stored': 0
                }
            
            logger.info(f"Fetched {len(df)} corporate events")
            
            # Store in database
            records_stored = self._store_data(df)
            
            logger.info(f"✅ Stored {records_stored} corporate events")
            
            return {
                'status': 'success',
                'records_fetched': len(df),
                'records_stored': records_stored,
                'date_range': f"{start_date.date()} to {end_date.date()}"
            }
            
        except Exception as e:
            logger.error(f"Error fetching corporate events: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'records_fetched': 0,
                'records_stored': 0
            }
    
    def _store_data(self, df: pd.DataFrame) -> int:
        """
        Store corporate events in database
        
        Returns:
            Number of records stored
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS corporate_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                company TEXT,
                event_type TEXT,
                event_subject TEXT,
                ex_date DATE,
                record_date DATE,
                bc_start_date DATE,
                bc_end_date DATE,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, event_subject, ex_date)
            )
        ''')
        
        records_stored = 0
        
        for _, row in df.iterrows():
            try:
                # Helper to get value or None
                def get_val(key, default=None):
                    val = row.get(key, default)
                    if pd.isna(val) or val == '-' or val == '':
                        return default
                    return val
                
                # Parse dates
                def parse_date(date_str):
                    if not date_str or pd.isna(date_str) or date_str == '-':
                        return None
                    try:
                        return datetime.strptime(date_str, '%d-%b-%Y').strftime('%Y-%m-%d')
                    except:
                        return None
                
                # Determine event type from subject
                subject = get_val('subject', '')
                event_type = 'Other'
                if 'dividend' in subject.lower():
                    event_type = 'Dividend'
                elif 'bonus' in subject.lower():
                    event_type = 'Bonus'
                elif 'split' in subject.lower():
                    event_type = 'Split'
                elif 'rights' in subject.lower():
                    event_type = 'Rights'
                elif 'buyback' in subject.lower():
                    event_type = 'Buyback'
                
                # Insert or replace
                cursor.execute('''
                    INSERT OR REPLACE INTO corporate_events
                    (symbol, company, event_type, event_subject,
                     ex_date, record_date, bc_start_date, bc_end_date, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    get_val('symbol'),
                    get_val('comp'),
                    event_type,
                    subject,
                    parse_date(get_val('exDate')),
                    parse_date(get_val('recordDate')),
                    parse_date(get_val('bcStartDate')),
                    parse_date(get_val('bcEndDate')),
                    get_val('details')
                ))
                records_stored += 1
                
            except Exception as e:
                logger.debug(f"Error storing corporate event row: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return records_stored


# Standalone script for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    service = CorporateEventsService()
    
    print("\n=== FETCHING CORPORATE EVENTS ===\n")
    results = service.fetch_and_store(days=90)
    
    print(f"\nStatus: {results['status']}")
    print(f"Records fetched: {results['records_fetched']}")
    print(f"Records stored: {results['records_stored']}")
    if 'date_range' in results:
        print(f"Date range: {results['date_range']}")
    
    # Verify database
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM corporate_events')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT symbol) FROM corporate_events')
    symbols = cursor.fetchone()[0]
    
    print(f"\n=== DATABASE VERIFICATION ===")
    print(f"Total records: {total:,}")
    print(f"Unique symbols: {symbols}")
    
    # Show event type breakdown
    cursor.execute('''
        SELECT event_type, COUNT(*) as cnt
        FROM corporate_events
        GROUP BY event_type
        ORDER BY cnt DESC
    ''')
    print(f"\nEvent types:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:,}")
    
    # Show latest events
    cursor.execute('''
        SELECT symbol, event_type, event_subject, ex_date
        FROM corporate_events
        WHERE ex_date IS NOT NULL
        ORDER BY ex_date DESC
        LIMIT 5
    ''')
    print(f"\nLatest 5 events:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} - {row[2][:50]}... on {row[3]}")
    
    conn.close()
