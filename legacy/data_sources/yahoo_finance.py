"""
Yahoo Finance API wrapper
"""

import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
from .base_source import DataSource
import logging

logger = logging.getLogger(__name__)


class YahooFinance(DataSource):
    """Yahoo Finance API wrapper."""
    
    def __init__(self):
        super().__init__("Yahoo_Finance")
    
    def _get_ticker(self, symbol: str):
        """Get Yahoo Finance ticker object."""
        yahoo_symbol = f"{symbol}.NS"
        return yf.Ticker(yahoo_symbol)
    
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company information."""
        try:
            ticker = self._get_ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'company_name': info.get('longName'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'website': info.get('website'),
                'description': info.get('longBusinessSummary'),
                'employees': info.get('fullTimeEmployees'),
                'source': self.name
            }
        except Exception as e:
            return self.handle_error(e, f"get_company_info({symbol})")
    
    def get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price data."""
        try:
            ticker = self._get_ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'last_price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'previous_close': info.get('previousClose'),
                'open': info.get('open') or info.get('regularMarketOpen'),
                'high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
                'low': info.get('dayLow') or info.get('regularMarketDayLow'),
                'volume': info.get('volume') or info.get('regularMarketVolume'),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'pb_ratio': info.get('priceToBook'),
                'dividend_yield': info.get('dividendYield'),
                'eps': info.get('trailingEps'),
                'week_52_high': info.get('fiftyTwoWeekHigh'),
                'week_52_low': info.get('fiftyTwoWeekLow'),
                'source': self.name
            }
        except Exception as e:
            return self.handle_error(e, f"get_price_data({symbol})")
    
    def get_historical_prices(self, symbol: str, period: str = '1y',
                            interval: str = '1d') -> Optional[pd.DataFrame]:
        """Get historical price data."""
        try:
            ticker = self._get_ticker(symbol)
            
            yahoo_period = {
                '1d': '1d', '5d': '5d', '1w': '5d', '1m': '1mo',
                '3m': '3mo', '6m': '6mo', '1y': '1y', '2y': '2y',
                '5y': '5y', 'max': 'max'
            }.get(period, '1y')
            
            df = ticker.history(period=yahoo_period)
            
            if df.empty:
                return None
            
            df = df.reset_index()
            df.columns = [col.lower() for col in df.columns]
            
            if 'date' not in df.columns and 'index' in df.columns:
                df = df.rename(columns={'index': 'date'})
            
            return df[['date', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            return self.handle_error(e, f"get_historical_prices({symbol})")