"""
Central configuration for the stock data system
"""

from pathlib import Path
from datetime import timedelta

# ============== DIRECTORIES ==============
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = BASE_DIR / ".cache"
EXPORT_DIR = BASE_DIR / "stock_data"

# Create directories if they don't exist
for directory in [DATA_DIR, CACHE_DIR, EXPORT_DIR]:
    directory.mkdir(exist_ok=True)

# ============== CACHE TTL (Time To Live) ==============
CACHE_TTL_PRICE = 60              # 1 minute for real-time price
CACHE_TTL_REALTIME = 60           # 1 minute for real-time data
CACHE_TTL_INTRADAY = 300          # 5 minutes for intraday
CACHE_TTL_DAILY = 3600            # 1 hour for daily data
CACHE_TTL_HISTORICAL = 86400      # 24 hours for historical
CACHE_TTL_FUNDAMENTAL = 86400     # 24 hours for fundamentals

# ============== RATE LIMITING ==============
RATE_LIMIT_NSE = 30               # NSE API calls per minute
RATE_LIMIT_SCREENER = 10          # Screener.in calls per minute
RATE_LIMIT_YAHOO = 100            # Yahoo Finance calls per minute

# ============== DATA FETCH SETTINGS ==============
DEFAULT_HISTORICAL_PERIOD = '1y'
DEFAULT_HISTORICAL_INTERVAL = '1d'
DEFAULT_INTRADAY_INTERVAL = '5m'

# ============== RETRY SETTINGS ==============
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# ============== EXPORT SETTINGS ==============
EXPORT_CSV_ENCODING = 'utf-8'
EXPORT_EXCEL_ENGINE = 'openpyxl'

# ============== LOGGING ==============
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = BASE_DIR / 'trading_system.log'

# ============== SYMBOLS ==============
# Popular indices
INDICES = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']

# Popular stocks by sector
IT_STOCKS = ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM', 'PERSISTENT', 'COFORGE', 'MPHASIS']
BANK_STOCKS = ['HDFCBANK', 'ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK']
AUTO_STOCKS = ['MARUTI', 'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'EICHERMOT']
PHARMA_STOCKS = ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'BIOCON']
FMCG_STOCKS = ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR']

ALL_POPULAR_STOCKS = IT_STOCKS + BANK_STOCKS + AUTO_STOCKS + PHARMA_STOCKS + FMCG_STOCKS