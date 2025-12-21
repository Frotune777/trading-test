"""
Source Parameter Adapters
Converts common parameters to source-specific formats
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SourceParameterAdapter:
    """Base class for parameter adaptation"""
    
    @staticmethod
    def period_to_dates(period: str) -> Tuple[datetime, datetime]:
        """Convert period string to start/end dates"""
        end_date = datetime.now()
        
        period_map = {
            '1m': timedelta(days=30),
            '3m': timedelta(days=90),
            '6m': timedelta(days=180),
            '1y': timedelta(days=365),
            '2y': timedelta(days=730),
            '5y': timedelta(days=1825),
            '10y': timedelta(days=3650),
            '20y': timedelta(days=7300),
            'max': timedelta(days=36500),  # ~100 years
        }
        
        delta = period_map.get(period, timedelta(days=365))
        start_date = end_date - delta
        
        return start_date, end_date


class YahooFinanceAdapter(SourceParameterAdapter):
    """
    Yahoo Finance parameter adapter
    
    Yahoo uses:
    - period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    - interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    """
    
    # Common to Yahoo period mapping
    PERIOD_MAP = {
        '1m': '1mo',
        '3m': '3mo',
        '6m': '6mo',
        '1y': '1y',
        '2y': '2y',
        '5y': '5y',
        '10y': '10y',
        '20y': '20y',  # Not directly supported, will use max
        'max': 'max'
    }
    
    # Common to Yahoo interval mapping
    INTERVAL_MAP = {
        '1d': '1d',
        '1w': '1wk',
        '1wk': '1wk',
        '1M': '1mo',
        '1mo': '1mo',
        '1h': '1h',
        '30m': '30m',
        '15m': '15m',
        '5m': '5m',
        '1m': '1m'
    }
    
    @classmethod
    def adapt_parameters(cls, period: str, interval: str) -> Dict[str, str]:
        """Convert common parameters to Yahoo format"""
        yahoo_period = cls.PERIOD_MAP.get(period, '1y')
        yahoo_interval = cls.INTERVAL_MAP.get(interval, '1d')
        
        # Yahoo doesn't support 20y, use max instead
        if period == '20y':
            yahoo_period = 'max'
        
        return {
            'period': yahoo_period,
            'interval': yahoo_interval
        }


class NSEAdapter(SourceParameterAdapter):
    """
    NSE parameter adapter
    
    NSE uses:
    - from_date, to_date: DD-MM-YYYY format
    - No direct interval support (daily data only for historical)
    """
    
    @classmethod
    def adapt_parameters(cls, period: str, interval: str) -> Dict[str, Any]:
        """Convert common parameters to NSE format"""
        start_date, end_date = cls.period_to_dates(period)
        
        # NSE date format: DD-MM-YYYY
        params = {
            'from_date': start_date.strftime('%d-%m-%Y'),
            'to_date': end_date.strftime('%d-%m-%Y')
        }
        
        # NSE typically only supports daily data for historical
        if interval not in ['1d', '1D']:
            logger.warning(f"NSE doesn't support interval '{interval}', using daily data")
            params['warning'] = f"NSE only supports daily data, interval '{interval}' not available"
        
        return params
    
    @classmethod
    def supports_interval(cls, interval: str) -> bool:
        """Check if NSE supports the given interval"""
        return interval.lower() in ['1d', 'daily']


class ScreenerAdapter(SourceParameterAdapter):
    """
    Screener.in parameter adapter
    
    Screener provides:
    - Quarterly/Annual results (limited historical depth)
    - No custom date ranges
    - No interval selection
    """
    
    @classmethod
    def adapt_parameters(cls, period: str, interval: str) -> Dict[str, Any]:
        """Convert common parameters to Screener format"""
        # Screener doesn't support custom periods/intervals
        # It provides pre-defined quarterly/annual data
        
        return {
            'data_type': 'quarterly' if interval in ['1M', '1mo', '3M', '3mo'] else 'annual',
            'warning': 'Screener provides limited pre-defined data, custom periods not supported'
        }
    
    @classmethod
    def supports_historical(cls) -> bool:
        """Screener doesn't support OHLCV historical data"""
        return False


# Registry of adapters
ADAPTERS = {
    'yahoo': YahooFinanceAdapter,
    'nse': NSEAdapter,
    'screener': ScreenerAdapter
}


def get_adapter(source: str) -> SourceParameterAdapter:
    """Get the appropriate adapter for a data source"""
    adapter = ADAPTERS.get(source.lower())
    if not adapter:
        logger.warning(f"No adapter found for source '{source}', using base adapter")
        return SourceParameterAdapter
    return adapter


def adapt_parameters(source: str, period: str, interval: str) -> Dict[str, Any]:
    """
    Adapt common parameters to source-specific format
    
    Args:
        source: Data source name ('yahoo', 'nse', 'screener')
        period: Common period (1m, 3m, 6m, 1y, 2y, 5y, 10y, 20y, max)
        interval: Common interval (1d, 1wk, 1mo, etc.)
    
    Returns:
        Dict with source-specific parameters
    """
    adapter = get_adapter(source)
    return adapter.adapt_parameters(period, interval)
