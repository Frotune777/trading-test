"""
data_sources/nse_complete.py
The unified, robust, and optimized data source for all NSE data.
Uses yfinance as the primary data source for NSE stocks.
"""
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import logging
import yfinance as yf

from .base_source import DataSource
from ..core.data_normalizer import DataNormalizer
from ..core.source_adapters import adapt_parameters

class NSEComplete(DataSource):
    def __init__(self):
        super().__init__("NSE_Complete")
        self.logger = logging.getLogger(__name__)
        self.normalizer = DataNormalizer()
        
        # Initialize NSE Master Data (lazy loading)
        self._nse_master = None
        
        self.logger.info("✅ NSEComplete initialized with yfinance backend and data normalizer")
        
    @property
    def nse_master(self):
        """Lazy load NSE Master Data"""
        if self._nse_master is None:
            try:
                from .nse_master_data import NSEMasterData
                self._nse_master = NSEMasterData()
                self._nse_master.download_symbol_master()
                self.logger.info("✅ NSE Master Data initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize NSE Master Data: {e}")
                self._nse_master = None
        return self._nse_master
        
    def _get_nse_ticker(self, symbol: str) -> str:
        """Convert symbol to NSE ticker format for yfinance"""
        # Remove any existing suffix
        clean_symbol = symbol.upper().replace('-EQ', '').replace('.NS', '')
        # Add .NS suffix for NSE stocks
        return f"{clean_symbol}.NS"

    def get_historical_prices(self, symbol: str, period: str = '1y', interval: str = '1d', source: str = 'auto') -> pd.DataFrame:
        """
        Get historical prices from selected source with proper parameter conversion
        
        Args:
            symbol: Stock symbol
            period: Time period (1m, 3m, 6m, 1y, 2y, 5y, 10y, 20y, max)
            interval: Data interval (1d, 1wk, 1mo, etc.)
            source: 'auto' (NSE→Yahoo fallback), 'nse', or 'yahoo'
        
        Returns:
            DataFrame with historical OHLCV data
        """
        if source == 'auto':
            # Try NSE first (for Indian stocks)
            self.logger.info(f"Auto mode: Trying NSE first for {symbol}")
            df = self._get_nse_historical(symbol, period, interval)
            if not df.empty:
                self.logger.info(f"✅ Got {len(df)} records from NSE for {symbol}")
                return df
            
            # Fallback to Yahoo if NSE fails
            self.logger.info(f"NSE unavailable for {symbol}, falling back to Yahoo Finance")
            return self._get_yahoo_historical(symbol, period, interval)
        
        elif source == 'nse':
            return self._get_nse_historical(symbol, period, interval)
        
        elif source == 'yahoo':
            return self._get_yahoo_historical(symbol, period, interval)
        
        else:
            self.logger.error(f"Unknown source: {source}")
            return pd.DataFrame()
    
    def _get_nse_historical(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """
        Fetch historical data from NSE using NSEMasterData
        """
        try:
            # Check if NSE Master Data is available
            if self.nse_master is None:
                self.logger.warning("NSE Master Data not available")
                return pd.DataFrame()
            
            # Use parameter adapter to convert to NSE format
            nse_params = adapt_parameters('nse', period, interval)
            
            # Log any warnings
            if 'warning' in nse_params:
                self.logger.warning(nse_params['warning'])
            
            # Convert date strings to datetime objects
            from datetime import datetime
            start_date = datetime.strptime(nse_params['from_date'], '%d-%m-%Y')
            end_date = datetime.strptime(nse_params['to_date'], '%d-%m-%Y')
            
            # Call NSE Master Data API
            self.logger.info(f"Fetching NSE data for {symbol} from {start_date} to {end_date}")
            df = self.nse_master.get_history(
                symbol=symbol,
                exchange='NSE',
                start=start_date,
                end=end_date,
                interval=interval
            )
            
            if df.empty:
                self.logger.warning(f"No data from NSE for {symbol}")
                return pd.DataFrame()
            
            # Normalize NSE data format to match our standard
            # NSE returns: index=Timestamp, columns=[Open, High, Low, Close, Volume]
            df = df.reset_index()
            df.rename(columns={'Timestamp': 'date'}, inplace=True)
            df.columns = [col.lower() for col in df.columns]
            
            # Remove timezone if present
            df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
            
            self.logger.info(f"✅ Got {len(df)} records from NSE for {symbol}")
            return df
            
        except Exception as e:
            self.handle_error(e, f"_get_nse_historical for {symbol}")
            return pd.DataFrame()
    
    def _get_yahoo_historical(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Get historical prices using yfinance with proper parameter conversion"""
        try:
            # Use parameter adapter to convert to Yahoo format
            yahoo_params = adapt_parameters('yahoo', period, interval)
            
            ticker = self._get_nse_ticker(symbol)
            stock = yf.Ticker(ticker)
            
            # Use adapted parameters
            df = stock.history(
                period=yahoo_params['period'],
                interval=yahoo_params['interval']
            )
            
            if df.empty:
                self.logger.warning(f"No historical data for {symbol}")
                return pd.DataFrame()
            
            # Reset index to make Date a column
            df = df.reset_index()
            
            # Standardize all column names to lowercase
            df.columns = [col.lower() for col in df.columns]
            
            # yfinance returns 'date' in the index, which becomes 'date' after reset_index and lowercase
            # Just ensure it's named 'date' for compatibility
            if 'date' not in df.columns:
                # If there's no 'date' column, the first column should be the date
                df.rename(columns={df.columns[0]: 'date'}, inplace=True)
            
            # Remove timezone info if present (for Excel compatibility)
            df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
            
            return df
        except Exception as e:
            self.handle_error(e, f"get_historical_prices for {symbol}")
            return pd.DataFrame()

    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get basic company information using yfinance
        """
        try:
            ticker = self._get_nse_ticker(symbol)
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Use normalizer if available, or return raw info
            if hasattr(self, 'normalizer'):
                # We can reuse normalize_complete_data or create a specific one for company info
                # For now, let's return the normalized data which includes company info
                return self.normalizer.normalize_complete_data(info, source='yahoo')
            
            return info
        except Exception as e:
            self.handle_error(e, f"get_company_info for {symbol}")
            return None

    def get_price_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price data using yfinance with data normalization
        """
        try:
            ticker = self._get_nse_ticker(symbol)
            stock = yf.Ticker(ticker)
            raw_info = stock.info
            
            # Normalize using data normalizer
            normalized_data = self.normalizer.normalize_complete_data(raw_info, source='yahoo')
            
            # Ensure symbol is set
            normalized_data['symbol'] = symbol
            
            return normalized_data
        except Exception as e:
            self.handle_error(e, f"get_price_data for {symbol}")
            return {}


class ScreenerMapper:
    """Field mapping for Screener.in data source"""
    
    # Key metrics from top-ratios section
    key_metrics_map = {
        'Market Cap': 'market_cap',
        'Current Price': 'last_price',
        'High / Low': '52w_high',  # Will need special handling
        'Stock P/E': 'pe_ratio',
        'Book Value': 'book_value',
        'Dividend Yield': 'dividend_yield',
        'ROCE': 'roce',
        'ROE': 'roe',
        'Face Value': 'face_value',
        'PEG Ratio': 'peg_ratio',
        'EPS': 'eps',
        'Debt to Equity': 'debt_to_equity',
        'Price to Book': 'price_to_book',
        'Sales': 'revenue',
        'Profit': 'net_income',
        'OPM %': 'operating_margin'
    }
    
    # Company info mappings
    company_info_map = {
        'symbol': 'symbol',
        'company_name': 'company_name',
        'sector': 'sector',
        'industry': 'industry'
    }
    
    @staticmethod
    def normalize_key_metrics(metrics_dict: dict) -> dict:
        """
        Normalize Screener key metrics to standard schema
        
        Args:
            metrics_dict: Raw metrics from Screener
            
        Returns:
            Normalized metrics dictionary
        """
        normalized = {}
        
        for screener_key, std_key in ScreenerMapper.key_metrics_map.items():
            if screener_key in metrics_dict:
                normalized[std_key] = metrics_dict[screener_key]
        
        return normalized

    def search(self, symbol: str, exchange='NSE', match: bool = False) -> pd.DataFrame:
        """
        Search for symbols (simple implementation using yfinance)
        """
        try:
            ticker = self._get_nse_ticker(symbol)
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return pd.DataFrame([{
                'symbol': symbol,
                'name': info.get('longName') or info.get('shortName'),
                'exchange': 'NSE',
                'currency': 'INR'
            }])
        except Exception as e:
            self.handle_error(e, f"search for {symbol}")
            return pd.DataFrame()

    
    # --- Other methods remain the same ---
    
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            ticker = self._get_nse_ticker(symbol)
            stock = yf.Ticker(ticker)
            return stock.info
        except Exception as e:
            return self.handle_error(e, f"get_company_info for {symbol}")

    def test_connection(self):
        """Test connection to yfinance"""
        try:
            # Test with a known symbol
            stock = yf.Ticker("RELIANCE.NS")
            info = stock.info
            return bool(info)
        except:
            return False