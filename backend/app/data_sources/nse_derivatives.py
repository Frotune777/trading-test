"""
data_sources/nse_derivatives.py
Source for Derivatives, Institutional Activity, and Market Breadth.
"""

from typing import Dict, Any, Optional
import pandas as pd
import requests
import logging
from datetime import datetime
import yfinance as yf
from nselib import capital_market

from .base_source import DataSource
from .nse_utils import NseUtils

logger = logging.getLogger(__name__)

class NSEDerivatives(DataSource):
    """
    Data source for NSE Derivatives, Institutional Activity, and Market Stats.
    Uses generic web scraping for FII/DII due to library limitations.
    """
    
    def __init__(self):
        super().__init__("NSE_Derivatives")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.nse_utils = NseUtils()
        
    def get_fii_dii_activity(self) -> Optional[Dict[str, Any]]:
        """
        Fetch FII/DII activity via scraping MoneyControl.
        Returns dictionary with Daily FII/DII stats.
        """
        try:
            url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
            response = requests.get(url, headers=self.headers, timeout=10)
            dfs = pd.read_html(response.content)
            
            if not dfs:
                logger.warning("No FII/DII tables found")
                return None
            
            # First table usually contains the daily summary
            df = dfs[0]
            
            # Basic parsing logic (assuming standard MoneyControl format)
            # Row 0 usually has "Month till date" or similar if not daily
            # We look for the row that corresponds to the latest date
            
            # For simplicity, we'll take the first row and parse it if it looks like data
            # The columns are MultiIndex: (FII, Gross Purchase), (FII, Gross Sales), etc.
            
            # Simple normalization for now
            data = {
                'date': datetime.now().strftime('%Y-%m-%d'), # Approximate as today if date parsing is complex
                'fii_net': 0.0,
                'dii_net': 0.0
            }
            
            # Flatten columns if MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() for col in df.columns.values]
            
            # Look for Net Purchase / Sales columns
            # This is highly dependent on table structure stability
            cols = [c for c in df.columns if 'Net' in c]
            
            if len(cols) >= 2:
                # Assuming first Net is FII, second is DII (check site layout)
                # FII is usually first group, DII second
                fii_val = df.iloc[0][cols[0]]
                dii_val = df.iloc[0][cols[1]]
                
                data['fii_net'] = self._parse_float(fii_val)
                data['dii_net'] = self._parse_float(dii_val)
                
            return data
            
        except Exception as e:
            self.handle_error(e, "get_fii_dii_activity")
            return None

    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Placeholder for base class requirement."""
        return None

    def get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Placeholder for base class requirement."""
        return None

    def get_historical_prices(self, symbol: str, period: str = '1y', interval: str = '1d') -> Optional[pd.DataFrame]:
        """Placeholder for base class requirement."""
        return None

    def get_market_breadth(self) -> Optional[Dict[str, int]]:
        """
        Calculate market breadth using nselib Bhav Copy.
        """
        try:
            # Fetch bhav copy for today (or latest valid day)
            # nselib usually handles date logic or we pass today
            # If today fails (holiday/weekend), maybe try logic to find last trading day?
            # For simplicity, let's try to get latest available (nselib might have a 'latest' flag or we try today)
            
            # Using specific date string logic might be brittle, so we rely on what worked in test_nselib.py
            # The test used "20-12-2024". We need a dynamic approach.
            
            # Try to fetch bhav copy for the last 5 days until successful
            bhav = None
            from datetime import timedelta
            
            for i in range(5):
                date_to_check = datetime.now() - timedelta(days=i)
                date_str = date_to_check.strftime('%d-%m-%Y')
                try:
                    bhav = capital_market.bhav_copy_equities(date_str)
                    if bhav is not None and not bhav.empty:
                        logger.info(f"Using Bhav Copy from {date_str}")
                        break
                except Exception:
                    continue
            
            if bhav is None or bhav.empty:
                logger.warning("Bhav Copy empty after 5 days lookback")
                return None
                
            # Columns usually: SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, LAST, PREVCLOSE...
            # Calculate Advances/Declines
            
            # Filter for EQ series only to avoid noise
            if 'SERIES' in bhav.columns:
                bhav = bhav[bhav['SERIES'] == 'EQ']
            
            # Calculate change
            # Ensure numeric
            close_col = 'CLOSE' if 'CLOSE' in bhav.columns else ' CLOSE_PRICE' # Check exact column name from lib
            prev_col = 'PREVCLOSE' if 'PREVCLOSE' in bhav.columns else ' PREV_CLOSE'
            
            # nselib columns are often standard, let's assume standard names or normalized
            # Based on nselib docs/usage: 'CLOSE_PRICE', 'PREV_CLOSE' or similar. 
            # In test step 340, verify col names if possible. 
            # Assuming standard NSE format:
            # Let's clean column names
            bhav.columns = [c.strip().upper() for c in bhav.columns]
            
            # Check for column names seen in logs: CLSPRIC, PRVSCLSGPRIC
            if 'CLSPRIC' in bhav.columns and 'PRVSCLSGPRIC' in bhav.columns:
                 bhav['change'] = pd.to_numeric(bhav['CLSPRIC'], errors='coerce') - pd.to_numeric(bhav['PRVSCLSGPRIC'], errors='coerce')
            elif 'CLOSE_PRICE' in bhav.columns:
                bhav['change'] = pd.to_numeric(bhav['CLOSE_PRICE'], errors='coerce') - pd.to_numeric(bhav['PREV_CLOSE'], errors='coerce')
            elif 'CLOSE' in bhav.columns:
                 bhav['change'] = pd.to_numeric(bhav['CLOSE'], errors='coerce') - pd.to_numeric(bhav['PREVCLOSE'], errors='coerce')
            else:
                logger.warning(f"Could not find price columns in bhav copy: {bhav.columns}")
                return None
            
            advances = len(bhav[bhav['change'] > 0])
            declines = len(bhav[bhav['change'] < 0])
            unchanged = len(bhav[bhav['change'] == 0])
            
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'advances': advances,
                'declines': declines,
                'unchanged': unchanged,
                'ratio': advances / declines if declines > 0 else advances
            }
            
        except Exception as e:
            self.handle_error(e, "get_market_breadth")
            return None

    def _parse_float(self, val):
        if isinstance(val, (int, float)): return float(val)
        try:
            return float(str(val).replace(',', '').replace('Cr', ''))
        except:
            return 0.0

    def get_option_chain(self, symbol: str, indices: bool = False):
        """
        Fetch full option chain using NseUtils.
        """
        try:
            return self.nse_utils.get_option_chain(symbol, indices=indices)
        except Exception as e:
            self.handle_error(e, f"get_option_chain({symbol})")
            return pd.DataFrame()
