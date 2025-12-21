"""
Standard Schema Definition
Defines the canonical field names and types for all stock data
"""

from typing import Dict, Type, Any
from datetime import datetime


class StandardSchema:
    """Standard internal schema for stock data across all sources"""
    
    # Price Data Fields
    PRICE_FIELDS: Dict[str, Type] = {
        'symbol': str,
        'last_price': float,
        'previous_close': float,
        'change': float,
        'change_percent': float,
        'open': float,
        'high': float,
        'low': float,
        'volume': int,
        'date': datetime,
        'vwap': float,
        'week_high_52': float,
        'week_low_52': float,
    }
    
    # Company Info Fields
    COMPANY_FIELDS: Dict[str, Type] = {
        'symbol': str,
        'company_name': str,
        'sector': str,
        'industry': str,
        'market_cap': float,
        'isin': str,
        'exchange': str,
    }
    
    # Fundamental Fields
    FUNDAMENTAL_FIELDS: Dict[str, Type] = {
        'pe_ratio': float,
        'pb_ratio': float,
        'roe': float,
        'roce': float,
        'dividend_yield': float,
        'book_value': float,
        'eps': float,
        'debt_to_equity': float,
        'current_ratio': float,
        'price_to_sales': float,
        'profit_margin': float,
    }
    
    # Historical Data Fields (for OHLCV data)
    HISTORICAL_FIELDS: Dict[str, Type] = {
        'date': datetime,
        'open': float,
        'high': float,
        'low': float,
        'close': float,
        'volume': int,
        'adjusted_close': float,
    }
    
    @classmethod
    def get_all_fields(cls) -> Dict[str, Type]:
        """Get all standard fields combined"""
        all_fields = {}
        all_fields.update(cls.PRICE_FIELDS)
        all_fields.update(cls.COMPANY_FIELDS)
        all_fields.update(cls.FUNDAMENTAL_FIELDS)
        return all_fields
