# utils/data_status.py

import sqlite3
from typing import List, Tuple
import logging
import pandas as pd

# CRITICAL FIX: Use the exact path provided by the user
try:
    from database.db_manager import DatabaseManager 
except ImportError:
    # This should now only happen if 'database' is misspelled or the file is missing.
    logging.error("CRITICAL: Failed to import DatabaseManager from 'database.db_manager'.")
    DatabaseManager = None 

logger = logging.getLogger(__name__)

# Cache the DatabaseManager instance (Singleton pattern)
_db_manager = None
# IMPORTANT: Ensure this path matches the initialization in your db_manager.py if different
DB_PATH = 'stock_data.db' 


def get_db_manager() -> DatabaseManager:
    """Singleton pattern to get the DatabaseManager instance."""
    global _db_manager
    
    if DatabaseManager is None:
        raise ConnectionError("DatabaseManager class is unavailable due to import error.")
        
    if _db_manager is None:
        try:
            # Initialize your SQLite Database Manager
            _db_manager = DatabaseManager(db_path=DB_PATH)
            logger.info("DatabaseManager initialized for status check.")
        except Exception as e:
            logger.error(f"Failed to initialize DatabaseManager: {e}")
            _db_manager = False # Indicate failure
            raise ConnectionError(f"Failed to connect to SQLite DB at {DB_PATH}") from e
    
    if _db_manager is False:
        raise ConnectionError(f"Database connection previously failed.")
        
    return _db_manager

# Complete list of tables from your initial post
ALL_TABLES = [
    "annual_results", "balance_sheet", "block_deals", "bulk_deals",
    "cash_flow", "companies", "corporate_actions", "corporate_announcements",
    "custom_metrics", "data_sources", "fii_dii_activity", "financial_ratios",
    "futures_data", "gainers_losers", "index_constituents", "index_history",
    "indices", "insider_trading", "intraday_prices", "latest_snapshot",
    "market_breadth", "market_depth", "ml_features", "option_chain",
    "option_chain_summary", "peers", "pre_market_data", "price_history",
    "quarterly_results", "results_calendar", "shareholding", "short_selling",
    "technical_indicators", "trading_holidays", "update_log"
]


def fetch_table_statistics() -> List[Tuple[str, int, str, str]]:
    """
    Fetches the record count for all tables using the DatabaseManager.
    
    :return: List of tuples: (table_name, count, status_emoji, quality_emoji)
    """
    stats = []
    
    try:
        db_manager = get_db_manager()
    except ConnectionError as e:
        print(f"CRITICAL DB CONNECTION ERROR: {e}")
        # Return all tables marked as error if the manager can't be initialized
        for table_name in ALL_TABLES:
            stats.append((table_name, 0, "🔴 Error", "❌ Failed"))
        return stats

    for table_name in ALL_TABLES:
        count = 0
        try:
            # THIS IS THE KEY: Calling the correct method from your db_manager
            count = db_manager.get_row_count(table_name)
            
            # --- Status and Quality Logic ---
            
            # 1. Determine Status Emoji
            status_emoji = "✅ Active" if count > 0 else "⚪ Empty"

            # 2. Determine Quality Emoji (based on the original table statistics logic)
            if count >= 1000:
                quality_emoji = "🟢 Rich"
            elif count >= 100:
                quality_emoji = "🟡 Good"
            elif count > 0:
                quality_emoji = "🟠 Limited" 
            else:
                quality_emoji = "⚪ Empty"
            
            # Refinements for small critical tables 
            if table_name in ["companies", "indices", "data_sources", "latest_snapshot", "update_log"] and count > 0:
                quality_emoji = "🟠 Limited"
            
            # ---------------------------------
            
            stats.append((table_name, count, status_emoji, quality_emoji))
            
        except sqlite3.OperationalError as e:
            # Handles "no such table" or similar SQLite errors
            print(f"Error checking table {table_name} (Operational): {e}")
            stats.append((table_name, 0, "🔴 Error", "❌ Failed"))
        except Exception as e:
            print(f"Unexpected error checking table {table_name}: {e}")
            stats.append((table_name, 0, "🔴 Error", "❌ Failed"))

    return stats