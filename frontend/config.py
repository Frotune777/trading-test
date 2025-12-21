# dashboard/config.py
"""
Configuration settings for Fortune Trading Dashboard
Version: 3.5 - Enhanced with Database Explorer
"""

from pathlib import Path
import os

# ============================================================================
# APP INFORMATION
# ============================================================================

APP_NAME = "Fortune Trading Dashboard"
VERSION = "3.5"
AUTHOR = "Fortune Trading Team"

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

PAGE_CONFIG = {
    "page_title": "Fortune Trading - Analytics",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"
}

# Available pages - Updated with Database Explorer
PAGES = {
    '📊 Analytics': 'Analytics',
    '📈 Trading': 'Trading',
    '💰 Portfolio': 'Portfolio',
    '📥 Data': 'Data',
    '🗄️ Database': 'Database',  # NEW - Database Explorer
    '🧮 Models': 'Models',
    '📊 MTF': 'MTF',  # Multi-Timeframe Analysis
    '🔍 Research': 'Research',
    '⚙️ Settings': 'Settings'
}

# ============================================================================
# FILE PATHS
# ============================================================================

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Database settings
DB_PATH = PROJECT_ROOT / 'stock_data.db'
DB_PATH_STR = str(DB_PATH)  # String version for compatibility

# Directory paths
BACKUP_DIR = PROJECT_ROOT / 'backups'
DATA_DIR = PROJECT_ROOT / 'data'
CACHE_DIR = PROJECT_ROOT / '.cache'
EXPORT_DIR = PROJECT_ROOT / 'exports'
LOG_DIR = PROJECT_ROOT / 'logs'

# Create directories if they don't exist
for directory in [BACKUP_DIR, DATA_DIR, CACHE_DIR, EXPORT_DIR, LOG_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# ============================================================================
# CACHE SETTINGS
# ============================================================================

CACHE_TTL = 3600  # 1 hour in seconds

# Detailed cache TTL for different data types
CACHE_TTL_DETAILED = {
    'price_data': 300,      # 5 minutes for real-time prices
    'company_info': 3600,   # 1 hour for company information
    'historical': 900,      # 15 minutes for historical data
    'fundamentals': 3600,   # 1 hour for fundamental data
    'technical': 600,       # 10 minutes for technical indicators
    'market_data': 180,     # 3 minutes for market-wide data
}

# ============================================================================
# COLOR SCHEME
# ============================================================================

COLORS = {
    'primary': '#4a90e2',
    'success': '#2ecc71',
    'danger': '#e74c3c',
    'warning': '#f39c12',
    'info': '#50c878',
    'bg_dark': '#0e1117',
    'bg_card': '#161b22',
    'border': '#2d3748',
    'text': '#e6edf3',
    'text_muted': '#8b949e',
    # Additional colors for charts
    'bullish': '#26a69a',
    'bearish': '#ef5350',
    'neutral': '#42a5f5'
}

# Chart colors palette
CHART_COLORS = ['#4a90e2', '#50c878', '#ff8c42', '#9b59b6', '#f39c12']

# Candlestick colors
CANDLESTICK_COLORS = {
    'increasing': '#26a69a',  # Green for bullish
    'decreasing': '#ef5350',  # Red for bearish
}

# ============================================================================
# MODEL CONFIGURATIONS
# ============================================================================

MODEL_TYPES = {
    'price_prediction': {
        'name': 'Price Prediction',
        'priority': '🔴 High',
        'use_cases': ['LSTM', 'ARIMA', 'Prophet', 'XGBoost'],
        'required_data': ['price_history', 'volume'],
        'lookback_days': 365
    },
    'volatility': {
        'name': 'Volatility Models',
        'priority': '🟠 Medium',
        'use_cases': ['GARCH', 'Stochastic Vol', 'Implied Vol Surface'],
        'required_data': ['price_history', 'option_chain'],
        'lookback_days': 180
    },
    'sentiment': {
        'name': 'Sentiment Analysis',
        'priority': '🟠 Medium',
        'use_cases': ['Institutional Sentiment', 'Market Breadth'],
        'required_data': ['fii_dii_activity', 'bulk_deals', 'market_breadth'],
        'lookback_days': 90
    },
    'event_driven': {
        'name': 'Event-Driven',
        'priority': '🟢 High Quality',
        'use_cases': ['Earnings', 'Dividends', 'Corporate Actions'],
        'required_data': ['corporate_actions', 'quarterly_results'],
        'lookback_days': 180
    },
    'portfolio': {
        'name': 'Portfolio Optimization',
        'priority': '🔴 High',
        'use_cases': ['Markowitz', 'Black-Litterman', 'Risk Parity'],
        'required_data': ['price_history', 'fundamentals'],
        'lookback_days': 365
    },
    'options': {
        'name': 'Options Trading',
        'priority': '🟠 Medium',
        'use_cases': ['Spreads', 'Volatility Trading', 'Greeks'],
        'required_data': ['option_chain', 'futures_data'],
        'lookback_days': 30
    }
}

# ============================================================================
# DATA SETTINGS
# ============================================================================

# Default timeframes for analysis
DEFAULT_TIMEFRAMES = ['1D', '1W', '1M', '3M', '6M', '1Y', 'ALL']

# MTF (Multi-Timeframe) settings
MTF_TIMEFRAMES = {
    'Intraday': ['1m', '5m', '15m', '30m', '1h', '4h'],
    'Daily': ['1D', '1W', '1M'],
    'Long-term': ['3M', '6M', '1Y', '2Y', '5Y']
}

# Popular stocks for quick access
POPULAR_STOCKS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
    'HINDUNILVR', 'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK',
    'LT', 'HCLTECH', 'AXISBANK', 'ASIANPAINT', 'MARUTI',
    'SUNPHARMA', 'TITAN', 'WIPRO', 'ULTRACEMCO', 'NESTLEIND'
]

# Stock categories
STOCK_CATEGORIES = {
    'NIFTY_50': ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK'],
    'BANKING': ['HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'AXISBANK', 'SBIN'],
    'IT': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM'],
    'PHARMA': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'BIOCON'],
    'AUTO': ['MARUTI', 'M&M', 'TATAMOTORS', 'BAJAJ-AUTO', 'HEROMOTOCO'],
    'FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR']
}

# ============================================================================
# TECHNICAL INDICATORS SETTINGS
# ============================================================================

TECHNICAL_INDICATORS = {
    'Moving Averages': {
        'SMA': [20, 50, 100, 200],
        'EMA': [12, 26, 50, 200],
        'WMA': [20, 50]
    },
    'Momentum': {
        'RSI': {'period': 14, 'overbought': 70, 'oversold': 30},
        'MACD': {'fast': 12, 'slow': 26, 'signal': 9},
        'Stochastic': {'k_period': 14, 'd_period': 3}
    },
    'Volatility': {
        'Bollinger Bands': {'period': 20, 'std_dev': 2},
        'ATR': {'period': 14},
        'Keltner Channels': {'period': 20, 'multiplier': 2}
    },
    'Volume': {
        'OBV': {},
        'Volume SMA': {'period': 20},
        'VWAP': {}
    }
}

# ============================================================================
# DISPLAY SETTINGS
# ============================================================================

# Chart settings
CHART_HEIGHT = 500
TABLE_HEIGHT = 400
MAX_TABLE_ROWS = 100

# Number formatting
NUMBER_FORMAT = {
    'price': '{:.2f}',
    'percent': '{:.2%}',
    'volume': '{:,.0f}',
    'market_cap': '{:.2f}Cr'
}

# Date formatting
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# ============================================================================
# API SETTINGS
# ============================================================================

# Rate limiting
RATE_LIMIT = {
    'requests_per_minute': 30,
    'delay_between_requests': 2,  # seconds
    'max_retries': 3,
    'retry_delay': 5  # seconds
}

# API endpoints (if needed)
API_ENDPOINTS = {
    'nse': 'https://www.nseindia.com',
    'screener': 'https://www.screener.in',
}

# ============================================================================
# NOTIFICATION SETTINGS
# ============================================================================

# Alert thresholds
ALERT_THRESHOLDS = {
    'price_change_percent': 5.0,
    'volume_spike_multiplier': 2.0,
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'unusual_activity': True,
    'earnings_reminder': 7,  # days before earnings
}

# Notification channels
NOTIFICATION_CHANNELS = {
    'dashboard': True,
    'email': False,  # Requires email setup
    'sound': True
}

# ============================================================================
# DATABASE EXPLORER SETTINGS
# ============================================================================

# Database Explorer specific settings
DB_EXPLORER = {
    'max_rows_display': 1000,
    'default_rows': 100,
    'enable_write': False,  # Safety: Only allow SELECT queries
    'export_formats': ['CSV', 'Excel', 'JSON'],
    'quick_queries': {
        'Latest Prices': "SELECT * FROM latest_snapshot ORDER BY change_percent DESC",
        'Top Gainers': "SELECT symbol, change_percent FROM latest_snapshot WHERE change_percent > 0 ORDER BY change_percent DESC LIMIT 10",
        'Top Losers': "SELECT symbol, change_percent FROM latest_snapshot WHERE change_percent < 0 ORDER BY change_percent ASC LIMIT 10",
        'Recent Updates': "SELECT * FROM update_log ORDER BY created_at DESC LIMIT 20",
        'Database Stats': "SELECT name as table_name, (SELECT COUNT(*) FROM sqlite_master WHERE name = m.name) as count FROM sqlite_master m WHERE type = 'table'"
    }
}

# ============================================================================
# VALIDATION SETTINGS
# ============================================================================

# Data validation rules
VALIDATION_RULES = {
    'price_data': {
        'required_columns': ['open', 'high', 'low', 'close', 'volume'],
        'price_checks': ['high >= low', 'high >= open', 'high >= close'],
        'volume_check': 'volume >= 0'
    },
    'fundamental_data': {
        'required_fields': ['revenue', 'profit', 'eps'],
        'ratio_limits': {
            'pe_ratio': (0, 1000),
            'pb_ratio': (0, 100),
            'debt_to_equity': (0, 10)
        }
    }
}

# ============================================================================
# EXPORT SETTINGS
# ============================================================================

# Export configurations
EXPORT_CONFIG = {
    'formats': ['CSV', 'Excel', 'JSON', 'Parquet', 'HTML'],
    'compression': True,
    'include_metadata': True,
    'timestamp_format': '%Y%m%d_%H%M%S',
    'default_path': EXPORT_DIR
}

# ============================================================================
# DEBUG SETTINGS
# ============================================================================

# Debug mode (set from environment or default)
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Logging settings
LOGGING = {
    'level': 'DEBUG' if DEBUG else 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': LOG_DIR / 'app.log',
    'max_bytes': 10485760,  # 10MB
    'backup_count': 5
}

# ============================================================================
# FEATURE FLAGS
# ============================================================================

# Enable/disable features
FEATURES = {
    'database_explorer': True,  # NEW feature
    'mtf_analysis': True,
    'ml_models': True,
    'backtesting': False,  # Coming soon
    'paper_trading': False,  # Coming soon
    'live_trading': False,  # Requires broker integration
    'news_sentiment': False,  # Requires news API
    'options_analytics': True,
    'portfolio_optimization': True
}