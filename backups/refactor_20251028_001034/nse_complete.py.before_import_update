"""
Complete NSE data source combining NseUtils + NSEMasterData
"""

import sys
from pathlib import Path

# Add external libs to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'external_libs'))

from nse_utils import NseUtils
from nse_master_data import NSEMasterData

from .base_source import DataSource
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class NSEComplete(DataSource):
    """
    Complete NSE data source using:
    - NseUtils: Fundamentals, corporate actions, live data
    - NSEMasterData: Historical prices, intraday, derivatives
    """
    
    def __init__(self):
        super().__init__("NSE_Complete")
        
        try:
            # Initialize both libraries
            self.fundamentals = NseUtils()
            self.historical = NSEMasterData()
            
            # Download symbol masters once
            self.historical.download_symbol_master()
            
            logger.info("✅ NSE Complete initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize NSE Complete: {e}")
            self.is_available = False
    
    # ==================== FUNDAMENTALS ====================
    
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company information."""
        try:
            data = self.fundamentals.equity_info(symbol)
            
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
            return self.handle_error(e, f"get_company_info({symbol})")
    
    def get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price data."""
        try:
            price_data = self.fundamentals.price_info(symbol)
            
            if not price_data:
                return None
            
            # Enhance with 52-week data
            week_52_data = self.fundamentals.get_52week_high_low(symbol)
            
            return {
                'symbol': symbol,
                'last_price': price_data.get('LastTradedPrice'),
                'previous_close': price_data.get('PreviousClose'),
                'change': price_data.get('Change'),
                'change_percent': price_data.get('PercentChange'),
                'open': price_data.get('Open'),
                'high': price_data.get('High'),
                'low': price_data.get('Low'),
                'vwap': price_data.get('VWAP'),
                'week_52_high': week_52_data.get('52 Week High') if week_52_data else None,
                'week_52_low': week_52_data.get('52 Week Low') if week_52_data else None,
                'source': self.name
            }
        except Exception as e:
            return self.handle_error(e, f"get_price_data({symbol})")
    
    # ==================== HISTORICAL DATA ====================
    
    def get_historical_prices(self, symbol: str, period: str = '1y',
                            interval: str = '1d') -> Optional[pd.DataFrame]:
        """
        Get historical OHLCV data.
        
        Args:
            symbol: NSE symbol
            period: '1d', '5d', '1m', '3m', '6m', '1y', '2y', '5y'
            interval: '1m', '5m', '15m', '30m', '1h', '1d', '1w', '1M'
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            
            period_map = {
                '1d': 1, '5d': 5, '1w': 7, '1m': 30, '3m': 90,
                '6m': 180, '1y': 365, '2y': 730, '5y': 1825
            }
            
            days = period_map.get(period, 365)
            start_date = end_date - timedelta(days=days)
            
            # Fetch data
            df = self.historical.get_history(
                symbol=symbol,
                exchange='NSE',
                start=start_date,
                end=end_date,
                interval=interval
            )
            
            if df is None or df.empty:
                logger.warning(f"No historical data for {symbol}")
                return None
            
            return df
            
        except Exception as e:
            return self.handle_error(e, f"get_historical_prices({symbol})")
    
    def get_intraday_data(self, symbol: str, interval: str = '5m') -> Optional[pd.DataFrame]:
        """
        Get today's intraday data.
        
        Args:
            symbol: NSE symbol
            interval: '1m', '3m', '5m', '10m', '15m', '30m', '1h'
        """
        return self.get_historical_prices(symbol, period='1d', interval=interval)
    
    # ==================== DERIVATIVES ====================
    
    def get_futures_data(self, symbol: str, expiry: str = None,
                        period: str = '1m', interval: str = '1d') -> Optional[pd.DataFrame]:
        """Get futures historical data."""
        try:
            if expiry is None:
                # Auto-detect current month expiry
                next_month = (datetime.now() + timedelta(days=30)).strftime('%y%b').upper()
                expiry = next_month
            
            futures_symbol = f"{symbol}{expiry}FUT"
            
            end_date = datetime.now()
            period_days = {'1d': 1, '1w': 7, '1m': 30, '3m': 90}
            start_date = end_date - timedelta(days=period_days.get(period, 30))
            
            return self.historical.get_history(
                symbol=futures_symbol,
                exchange='NFO',
                start=start_date,
                end=end_date,
                interval=interval
            )
            
        except Exception as e:
            return self.handle_error(e, f"get_futures_data({symbol})")
    
    def get_options_data(self, symbol: str, strike: int, option_type: str,
                        expiry: str = None, interval: str = '5m') -> Optional[pd.DataFrame]:
        """Get options historical data."""
        try:
            if expiry is None:
                next_month = (datetime.now() + timedelta(days=30)).strftime('%y%b').upper()
                expiry = next_month
            
            option_symbol = f"{symbol}{expiry}{strike}{option_type}"
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            return self.historical.get_history(
                symbol=option_symbol,
                exchange='NFO',
                start=start_date,
                end=end_date,
                interval=interval
            )
            
        except Exception as e:
            return self.handle_error(e, f"get_options_data({symbol})")
    
    # ==================== MARKET DATA ====================
    
    def get_option_chain(self, symbol: str, indices: bool = True) -> Optional[pd.DataFrame]:
        """Get full option chain."""
        try:
            return self.fundamentals.get_option_chain(symbol, indices=indices)
        except Exception as e:
            return self.handle_error(e, f"get_option_chain({symbol})")
    
    def get_market_depth(self, symbol: str) -> Optional[Dict]:
        """Get bid/ask depth."""
        try:
            return self.fundamentals.get_market_depth(symbol)
        except Exception as e:
            return self.handle_error(e, f"get_market_depth({symbol})")
    
    # ==================== CORPORATE ACTIONS ====================
    
    def get_corporate_actions(self, from_date: str = None, to_date: str = None,
                             filter: str = None) -> Optional[pd.DataFrame]:
        """Get corporate actions."""
        try:
            return self.fundamentals.get_corporate_action(
                from_date_str=from_date,
                to_date_str=to_date,
                filter=filter
            )
        except Exception as e:
            return self.handle_error(e, "get_corporate_actions")
    
    def get_bulk_deals(self, from_date: str = None, to_date: str = None) -> Optional[pd.DataFrame]:
        """Get bulk deals."""
        try:
            return self.fundamentals.get_bulk_deals(from_date=from_date, to_date=to_date)
        except Exception as e:
            return self.handle_error(e, "get_bulk_deals")
    
    def get_insider_trading(self, from_date: str = None, to_date: str = None) -> Optional[pd.DataFrame]:
        """Get insider trading data."""
        try:
            return self.fundamentals.get_insider_trading(from_date=from_date, to_date=to_date)
        except Exception as e:
            return self.handle_error(e, "get_insider_trading")
    
    # ==================== ENHANCED FEATURES ====================
    
    def get_complete_data(self, symbol: str) -> Dict[str, Any]:
        """Get complete dataset for a symbol."""
        logger.info(f"📊 Fetching complete data for {symbol}")
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'company_info': self.get_company_info(symbol),
            'current_price': self.get_price_data(symbol),
            'historical_daily': self.get_historical_prices(symbol, period='1y', interval='1d'),
            'intraday_5m': self.get_intraday_data(symbol, interval='5m'),
            'corporate_actions': self.get_corporate_actions()
        }