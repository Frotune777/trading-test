"""
data_sources/nse_complete.py
The unified, robust, and optimized data source for all NSE data.
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime
import logging

# Add external_libs to path
sys.path.insert(0, str(Path(__file__).parent.parent / "external_libs"))

try:
    from nse_utils import NseUtils
    from nse_master_data import NSEMasterData
except ImportError as e:
    logging.error(f"Could not import from external_libs: {e}.")
    class NseUtils: pass
    class NSEMasterData: pass

from .base_source import DataSource

class NSEComplete(DataSource):
    def __init__(self):
        super().__init__("NSE_Complete")
        self.logger = logging.getLogger(__name__)
        
        try:
            self.nse = NseUtils()
            self.master = NSEMasterData()
            self.master.download_symbol_master()
            self.logger.info("✅ NSE Master Data download initiated.")
        except Exception as e:
            self.logger.critical(f"Failed to initialize NSEComplete components: {e}")
            if not hasattr(self, 'nse'): self.nse = None
            if not hasattr(self, 'master'): self.master = None

    # --- FIX START (V4) ---
    # Implement abstract methods by *translating* calls to the
    # correctly-named methods on the wrapped objects.

    def get_historical_prices(self, symbol: str, period: str = '1y', interval: str = '1d') -> pd.DataFrame:
        """
        Fulfills abstract method by mapping to self.master.get_history().
        FIXED: Passes datetime objects instead of date strings.
        """
        if not (hasattr(self, 'master') and self.master):
            self.handle_error(AttributeError("NSEMasterData component not initialized"), "get_historical_prices")
            return pd.DataFrame()

        try:
            # Calculate start and end as datetime objects
            end_date = datetime.now()
            if period == '1y':
                start_date = end_date - pd.DateOffset(years=1)
            elif period == '6m':
                start_date = end_date - pd.DateOffset(months=6)
            elif period == '3m':
                start_date = end_date - pd.DateOffset(months=3)
            elif period == '1m':
                start_date = end_date - pd.DateOffset(months=1)
            else:
                start_date = end_date - pd.DateOffset(years=1) # Default
            
            # --- THIS IS THE FIX FOR THE 'timestamp' ERROR ---
            # Pass datetime objects directly to get_history
            
            # Assume it's an equity and append '-EQ' for lookup
            search_sym = symbol
            if not search_sym.upper().endswith('-EQ'):
                 search_sym = search_sym + '-EQ'
            
            df = self.master.get_history(
                symbol=search_sym,
                exchange='NSE',
                start=start_date, # Pass datetime object
                end=end_date,     # Pass datetime object
                interval=interval
            )

            # Fallback: If it returns empty, it might be an index (like 'NIFTY 50')
            if df.empty:
                df = self.master.get_history(
                    symbol=symbol, # Pass the original symbol
                    exchange='NSE',
                    start=start_date, # Pass datetime object
                    end=end_date,     # Pass datetime object
                    interval=interval
                )
            return df
        
        except Exception as e:
            self.handle_error(e, f"get_historical_prices for {symbol}")
            return pd.DataFrame()

    def get_price_data(self, symbol: str) -> pd.DataFrame:
        """
        Fulfills abstract method by mapping to self.nse.price_info().
        """
        if not (hasattr(self, 'nse') and self.nse):
            self.handle_error(AttributeError("NseUtils component not initialized"), "get_price_data")
            return pd.DataFrame()
        
        try:
            # Call the correct underlying method 'price_info'
            return self.nse.price_info(symbol)
        except Exception as e:
            self.handle_error(e, f"get_price_data for {symbol}")
            return pd.DataFrame()



    def search(self, symbol: str, exchange='NSE', match: bool = False) -> pd.DataFrame:
        """
        Performs a search using the master list.
        Intelligently adds '-EQ' suffix for NSE equity validation.
        """
        if not self.master:
            self.handle_error(Exception("NSEMasterData not initialized"), "search")
            return pd.DataFrame()

        search_term = symbol
        if exchange == 'NSE':
            if not search_term.upper().endswith('-EQ'):
                search_term = search_term + '-EQ'
        
        try:
            # The method is 'search'
            result_df = self.master.search(symbol=search_term, exchange=exchange, match=match)
            
            # Fallback for indices
            if result_df.empty and '-' in search_term:
                result_df = self.master.search(symbol=symbol, exchange=exchange, match=match)

            if not result_df.empty:
                rename_map = {
                    'TradingSymbol': 'symbol_raw',
                    'Description': 'name'
                }
                result_df = result_df.rename(columns=rename_map)
                if 'symbol_raw' in result_df.columns:
                    result_df['symbol'] = result_df['symbol_raw'].str.replace('-EQ', '', regex=False)

            return result_df
        
        except Exception as e:
            self.handle_error(e, f"search for {symbol}")
            return pd.DataFrame()

    
    # --- Other methods remain the same ---
    
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not self.nse: return self.handle_error(Exception("NseUtils not initialized"), "get_company_info")
        try:
            return self.nse.equity_info(symbol)
        except Exception as e:
            return self.handle_error(e, f"get_company_info for {symbol}")

    def __getattr__(self, name):
        """
        Delegate calls to the wrapped nse or master instances.
        """
        if hasattr(self, 'nse') and self.nse and hasattr(self.nse, name):
            return getattr(self.nse, name)
        if hasattr(self, 'master') and self.master and hasattr(self.master, name):
            return getattr(self.master, name)
        
        raise AttributeError(f"'{type(self).__name__}' object or its wrapped 'nse'/'master' objects have no attribute '{name}'")