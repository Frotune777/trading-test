# dashboard/utils/data_loader.py
"""
Data loading and caching utilities
Updated to export get_nse for validation
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import sys

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db_manager import DatabaseManager
from database.updater import DataUpdater
from data_sources.nse_complete import NSEComplete


@st.cache_resource
def get_database():
    """Get cached database instance"""
    return DatabaseManager()


@st.cache_resource
def get_nse():
    """Get cached NSE data source - NOW EXPORTED"""
    return NSEComplete()


@st.cache_resource
def get_updater():
    """Get cached updater instance"""
    return DataUpdater()


@st.cache_data(ttl=3600)
def load_stock_data(symbol: str):
    """Load complete stock data with caching"""
    db = get_database()
    
    try:
        snapshot = db.get_snapshot(symbol)
        price_history = db.get_price_history(symbol, days=365)
        quarterly = db.get_quarterly_results(symbol, limit=8)
        annual = db.get_annual_results(symbol, limit=5)
        shareholding = db.get_shareholding(symbol, limit=4)
        peers = db.get_peers(symbol)
        
        return {
            'snapshot': snapshot,
            'price_history': price_history,
            'quarterly': quarterly,
            'annual': annual,
            'shareholding': shareholding,
            'peers': peers,
            'last_update': db.get_last_update(symbol)
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def calculate_metrics(price_history: pd.DataFrame, snapshot: dict):
    """Calculate key performance metrics"""
    from dashboard.utils.formatters import safe_num
    
    current_price = safe_num(snapshot.get('current_price') if snapshot else None, 0)
    change_percent = safe_num(snapshot.get('change_percent') if snapshot else None, 0)
    
    if price_history.empty or len(price_history) < 2:
        return {
            'total_return': 0,
            'volatility': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'avg_volume': 0,
            'current_price': current_price,
            'change_percent': change_percent
        }
    
    try:
        first_close = safe_num(price_history['close'].iloc[0], 0)
        last_close = safe_num(price_history['close'].iloc[-1], 0)
        
        if first_close > 0:
            total_return = ((last_close / first_close) - 1) * 100
        else:
            total_return = 0
        
        daily_returns = price_history['close'].pct_change().dropna()
        if len(daily_returns) > 0:
            volatility = daily_returns.std() * np.sqrt(252) * 100
        else:
            volatility = 0
        
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100
        max_drawdown = safe_num(drawdown.min(), 0)
        
        if len(daily_returns) > 0 and daily_returns.std() > 0:
            excess_returns = daily_returns.mean() * 252 - 0.06
            sharpe = excess_returns / (daily_returns.std() * np.sqrt(252))
        else:
            sharpe = 0
        
        avg_volume = int(safe_num(price_history['volume'].mean(), 0))
        
        return {
            'total_return': round(safe_num(total_return, 0), 2),
            'volatility': round(safe_num(volatility, 0), 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(safe_num(sharpe, 0), 2),
            'avg_volume': avg_volume,
            'current_price': current_price,
            'change_percent': change_percent
        }
    except Exception as e:
        return {
            'total_return': 0,
            'volatility': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'avg_volume': 0,
            'current_price': current_price,
            'change_percent': change_percent
        }