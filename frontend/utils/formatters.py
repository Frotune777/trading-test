"""
Data Formatting Utilities - Financial Data Presentation
Ensures consistent, professional formatting across the application
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Optional, Union


def safe_num(value: Any, default: float = 0) -> float:
    """
    Safely convert any value to float
    
    Critical for financial data where None, NaN, or string values
    can cause calculation errors
    
    Args:
        value: Input value (can be int, float, str, None, NaN)
        default: Default value if conversion fails
    
    Returns:
        Float value or default
    """
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_format_currency(
    value: Any, 
    decimals: int = 2, 
    default: str = 'N/A',
    symbol: str = '₹'
) -> str:
    """
    Format value as currency with symbol
    
    Examples:
        1234.56 -> "₹1,234.56"
        None -> "N/A"
    """
    num = safe_num(value, None)
    if num is None:
        return default
    return f"{symbol}{num:,.{decimals}f}"


def safe_format_percent(
    value: Any, 
    decimals: int = 2, 
    default: str = 'N/A',
    include_sign: bool = False
) -> str:
    """
    Format value as percentage
    
    Examples:
        15.5 -> "15.50%"
        -2.3 -> "-2.30%"
    """
    num = safe_num(value, None)
    if num is None:
        return default
    
    sign = '+' if include_sign and num > 0 else ''
    return f"{sign}{num:.{decimals}f}%"


def safe_format_number(
    value: Any, 
    decimals: int = 0, 
    default: str = 'N/A',
    abbreviate: bool = False
) -> str:
    """
    Format value as number with thousand separators
    
    Args:
        abbreviate: If True, use K/M/B/T suffixes
    
    Examples:
        1234567 -> "1,234,567"
        1234567 (abbreviated) -> "1.23M"
    """
    num = safe_num(value, None)
    if num is None:
        return default
    
    if abbreviate:
        abs_num = abs(num)
        if abs_num >= 1e12:
            return f"{num/1e12:.2f}T"
        elif abs_num >= 1e9:
            return f"{num/1e9:.2f}B"
        elif abs_num >= 1e6:
            return f"{num/1e6:.2f}M"
        elif abs_num >= 1e3:
            return f"{num/1e3:.2f}K"
    
    return f"{num:,.{decimals}f}"


def safe_get_dict_value(
    data: dict, 
    key: str, 
    default: str = 'N/A', 
    format_func: Optional[callable] = None
) -> Any:
    """
    Safely retrieve and optionally format dictionary value
    
    Args:
        data: Source dictionary
        key: Key to retrieve
        default: Default if key missing or None
        format_func: Optional formatting function
    """
    if not data:
        return default
    
    value = data.get(key)
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    
    if format_func:
        try:
            return format_func(value)
        except:
            return default
    
    return value


def format_time_ago(dt: Union[datetime, str, None]) -> str:
    """
    Format datetime as human-readable "time ago"
    
    Examples:
        5 minutes ago -> "5m ago"
        2 hours ago -> "2h ago"
        3 days ago -> "3d ago"
        Never updated -> "Never"
    
    Critical for monitoring data freshness in trading systems
    """
    if not dt:
        return 'Never'
    
    # Handle string datetime
    if isinstance(dt, str):
        try:
            dt = pd.to_datetime(dt)
        except:
            return 'Unknown'
    
    now = datetime.now()
    
    # Make both timezone-naive for comparison
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    
    age = now - dt
    
    seconds = age.total_seconds()
    
    if seconds < 0:
        return 'Just now'
    elif seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        return f"{int(seconds/60)}m ago"
    elif seconds < 86400:
        return f"{int(seconds/3600)}h ago"
    elif seconds < 604800:
        return f"{int(seconds/86400)}d ago"
    elif seconds < 2592000:
        return f"{int(seconds/604800)}w ago"
    else:
        return f"{int(seconds/2592000)}mo ago"


def format_large_number(value: Any) -> str:
    """
    Format large numbers with Indian numbering system
    
    Examples:
        1234567 -> "12.35 Lakhs"
        12345678 -> "1.23 Crores"
    """
    num = safe_num(value, None)
    if num is None:
        return 'N/A'
    
    abs_num = abs(num)
    
    if abs_num >= 1e7:  # Crores
        return f"{num/1e7:.2f} Cr"
    elif abs_num >= 1e5:  # Lakhs
        return f"{num/1e5:.2f} L"
    elif abs_num >= 1e3:  # Thousands
        return f"{num/1e3:.2f} K"
    else:
        return f"{num:.2f}"


def parse_indian_number(value: str) -> Optional[float]:
    """
    Parse Indian formatted numbers
    
    Examples:
        "₹1,23,456.78" -> 123456.78
        "12.5 Cr" -> 125000000.0
        "45.2 L" -> 4520000.0
    """
    if not value:
        return None
    
    # Remove currency symbols
    value = str(value).replace('₹', '').replace('Rs.', '').strip()
    
    # Handle abbreviations
    multiplier = 1
    if 'Cr' in value or 'cr' in value:
        multiplier = 1e7
        value = value.replace('Cr', '').replace('cr', '').strip()
    elif 'L' in value or 'l' in value or 'Lakh' in value:
        multiplier = 1e5
        value = value.replace('L', '').replace('l', '').replace('Lakh', '').strip()
    elif 'K' in value or 'k' in value:
        multiplier = 1e3
        value = value.replace('K', '').replace('k', '').strip()
    
    # Remove commas
    value = value.replace(',', '')
    
    try:
        return float(value) * multiplier
    except:
        return None


def format_market_cap(value: Any) -> str:
    """
    Format market cap in standard financial notation
    
    Uses Cr (Crores) for Indian markets
    """
    num = safe_num(value, None)
    if num is None:
        return 'N/A'
    
    if num >= 1e7:
        return f"₹{num/1e7:,.0f} Cr"
    elif num >= 1e5:
        return f"₹{num/1e5:,.0f} L"
    else:
        return f"₹{num:,.0f}"


def color_code_change(value: float) -> str:
    """
    Return color class based on value (for price changes)
    
    Returns:
        'price-up', 'price-down', or 'price-neutral'
    """
    if value > 0:
        return 'price-up'
    elif value < 0:
        return 'price-down'
    else:
        return 'price-neutral'