"""
data_sources/nse_complete.py
The unified, robust, and optimized data source for all NSE data.
Uses NSEMasterData as the PRIMARY and PERMANENT data source.

IMPORTANT: This uses NSE Charting API directly via NSEMasterData.
DO NOT replace with yfinance - NSEMasterData is more reliable for Indian stocks.
"""
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import logging

from .base_source import DataSource
from .nse_master_data import NSEMasterData
from .nse_utils import NseUtils
from ..core.data_normalizer import DataNormalizer

logger = logging.getLogger(__name__)


class NSEComplete(DataSource):
    """
    Complete NSE data source using NSEMasterData and NseUtils.
    
    Data Sources:
    - NSEMasterData: Historical OHLCV data from NSE Charting API
    - NseUtils: Live prices, fundamentals, corporate actions
    
    PERMANENT IMPLEMENTATION - DO NOT REPLACE WITH YFINANCE
    """
    
    def __init__(self):
        super().__init__("NSE_Complete")
        self.logger = logging.getLogger(__name__)
        self.normalizer = DataNormalizer()
        
        try:
            # Initialize NSE libraries
            self.nse_master = NSEMasterData()
            self.nse_utils = NseUtils()
            
            # Download symbol masters
            self.nse_master.download_symbol_master()
            
            self.logger.info("✅ NSEComplete initialized with NSEMasterData and NseUtils")
        except Exception as e:
            self.logger.error(f"Failed to initialize NSE libraries: {e}")
            self.nse_master = None
            self.nse_utils = None

    def get_historical_prices(self, symbol: str, period: str = '1y', interval: str = '1d', source: str = 'nse') -> pd.DataFrame:
        """
        Get historical prices using NSEMasterData (NSE Charting API).
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            period: Time period (1d, 5d, 1m, 3m, 6m, 1y, 2y, 5y)
            interval: Data interval (1m, 3m, 5m, 10m, 15m, 30m, 1h, 1d, 1w, 1M)
            source: IGNORED - always uses NSE (kept for API compatibility)
            
        Returns:
            DataFrame with historical OHLCV data
            
        Note:
            - Uses NSE Charting API via NSEMasterData
            - Supports all intervals including intraday
            - More reliable than yfinance for Indian stocks
        """
        if self.nse_master is None:
            self.logger.error("NSEMasterData not initialized")
            return pd.DataFrame()
        
        try:
            # Calculate date range
            end_date = datetime.now()
            
            period_map = {
                '1d': 1, '5d': 5, '1w': 7, '1m': 30, '3m': 90,
                '6m': 180, '1y': 365, '2y': 730, '5y': 1825
            }
            
            days = period_map.get(period, 365)
            start_date = end_date - timedelta(days=days)
            
            # Fetch from NSE Charting API
            self.logger.info(f"Fetching {symbol} from NSE: {interval} interval, {period} period")
            df = self.nse_master.get_history(
                symbol=symbol,
                exchange='NSE',
                start=start_date,
                end=end_date,
                interval=interval
            )
            
            if df is None or df.empty:
                self.logger.warning(f"No historical data for {symbol} from NSE")
                return pd.DataFrame()
            
            # Standardize column names
            df = df.reset_index()
            if 'Timestamp' in df.columns:
                df.rename(columns={'Timestamp': 'date'}, inplace=True)
            
            # Ensure lowercase column names
            df.columns = [col.lower() for col in df.columns]
            
            # Remove timezone if present - handle NaT values properly
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                # Only tz_localize if not already timezone-naive and not NaT
                if df['date'].dt.tz is not None:
                    df['date'] = df['date'].dt.tz_localize(None)
            
            self.logger.info(f"✅ Got {len(df)} records from NSE for {symbol}")
            return df
            
        except Exception as e:
            self.handle_error(e, f"get_historical_prices for {symbol}")
            return pd.DataFrame()

    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get company information using NseUtils.
        """
        if self.nse_utils is None:
            return None
            
        try:
            data = self.nse_utils.equity_info(symbol)
            
            if not data:
                return None
            
            return {
                'symbol': symbol,
                'company_name': data.get('info', {}).get('companyName'),
                'industry': data.get('metadata', {}).get('industry'),
                'sector': data.get('info', {}).get('sector'),
                'isin': data.get('info', {}).get('isin'),
                'listing_date': data.get('info', {}).get('listingDate'),
                'source': self.name
            }
        except Exception as e:
            self.handle_error(e, f"get_company_info for {symbol}")
            return None

    def get_price_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price data using NseUtils.
        """
        if self.nse_utils is None:
            return {}
            
        try:
            price_data = self.nse_utils.price_info(symbol)
            
            if not price_data:
                return {}
            
            # Get 52-week data
            week_52_data = self.nse_utils.get_52week_high_low(symbol)
            
            result = {
                'symbol': symbol,
                'ltp': price_data.get('LastTradedPrice'),
                'last_price': price_data.get('LastTradedPrice'),
                'previous_close': price_data.get('PreviousClose'),
                'change': price_data.get('Change'),
                'change_percent': price_data.get('PercentChange'),
                'open': price_data.get('Open'),
                'high': price_data.get('High'),
                'low': price_data.get('Low'),
                'vwap': price_data.get('VWAP'),
                'volume': price_data.get('TotalTradedVolume'),
                'week_52_high': week_52_data.get('52 Week High') if week_52_data else None,
                'week_52_low': week_52_data.get('52 Week Low') if week_52_data else None,
                'source': self.name
            }
            
            # Normalize using data normalizer
            normalized_data = self.normalizer.normalize_complete_data(result, source='nse')
            normalized_data['symbol'] = symbol
            
            return normalized_data
            
        except Exception as e:
            self.handle_error(e, f"get_price_data for {symbol}")
            return {}

    def get_option_chain(self, symbol: str, indices: bool = True) -> Optional[pd.DataFrame]:
        """Get option chain data."""
        if self.nse_utils is None:
            return None
            
        try:
            return self.nse_utils.get_option_chain(symbol, indices=indices)
        except Exception as e:
            self.handle_error(e, f"get_option_chain for {symbol}")
            return None

    def get_insider_trading(self, from_date: str = None, to_date: str = None) -> Optional[pd.DataFrame]:
        """Get insider trading data."""
        if self.nse_utils is None:
            return None
            
        try:
            return self.nse_utils.get_insider_trading(from_date=from_date, to_date=to_date)
        except Exception as e:
            self.handle_error(e, "get_insider_trading")
            return None

    def test_connection(self):
        """Test connection to NSE."""
        try:
            if self.nse_master is None:
                return False
            
            # Try to fetch a known symbol
            df = self.nse_master.get_history(
                symbol="RELIANCE",
                exchange="NSE",
                start=datetime.now() - timedelta(days=7),
                end=datetime.now(),
                interval='1d'
            )
            return not df.empty
        except:
            return False


# For backward compatibility - map old yfinance methods
class ScreenerMapper:
    """Field mapping for Screener.in data source"""
    
    key_metrics_map = {
        'Market Cap': 'market_cap',
        'Current Price': 'last_price',
        'High / Low': '52w_high',
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
    
    @staticmethod
    def normalize_key_metrics(metrics_dict: dict) -> dict:
        """Normalize Screener key metrics to standard schema"""
        normalized = {}
        for screener_key, std_key in ScreenerMapper.key_metrics_map.items():
            if screener_key in metrics_dict:
                normalized[std_key] = metrics_dict[screener_key]
        return normalized