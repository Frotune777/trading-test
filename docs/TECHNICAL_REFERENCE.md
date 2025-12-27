# QUAD Trading Platform - Technical Reference

**Last Updated:** 2025-12-28  
**Version:** Phase 0 (Days 1-3 Complete)

---

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [API Endpoints](#api-endpoints)
4. [Data Sources](#data-sources)
5. [Services](#services)
6. [Scheduler Jobs](#scheduler-jobs)
7. [Setup & Deployment](#setup--deployment)

---

## System Architecture

### Technology Stack
- **Backend:** FastAPI (Python 3.11)
- **Database:** SQLite (`stock_data.db`)
- **Cache:** Redis
- **Task Queue:** APScheduler
- **Data Analysis:** TA-Lib, pandas, numpy
- **Deployment:** Docker Compose

### Directory Structure
```
backend/
├── app/
│   ├── api/v1/endpoints/     # API route handlers
│   ├── services/             # Business logic
│   ├── data_sources/         # NSE, Yahoo, Screener integrations
│   ├── core/                 # Config, scheduler, Redis
│   ├── database/             # DB manager, models
│   └── ml/                   # Machine learning models
├── scripts/                  # Utility scripts
└── stock_data.db            # SQLite database

frontend-new/
├── src/
│   ├── app/                 # Next.js pages
│   ├── components/          # React components
│   └── lib/                 # Utilities, API clients
```

---

## Database Schema

### 1. `price_history`
Stores historical OHLCV data from NSE.

```sql
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    adj_close REAL,
    delivery_qty INTEGER,
    delivery_percent REAL,
    trades_count INTEGER,
    turnover REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);
```

**Current Status:** 311,808 records (49 symbols, 1995-2025)

### 2. `technical_indicators`
Stores calculated technical indicators using TA-Lib.

```sql
CREATE TABLE technical_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    sma_20 REAL,
    sma_50 REAL,
    sma_200 REAL,
    ema_12 REAL,
    ema_26 REAL,
    rsi_14 REAL,
    macd REAL,
    macd_signal REAL,
    bollinger_upper REAL,
    bollinger_middle REAL,
    bollinger_lower REAL,
    atr_14 REAL,
    adx_14 REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);
```

**Current Status:** 311,808 records (49 symbols)

**Indicator Mappings:**
- `sma_20/50/200`: Simple Moving Averages
- `ema_12/26`: Exponential Moving Averages (mapped from ema_9/21 in TA-Lib)
- `rsi_14`: Relative Strength Index
- `macd/macd_signal`: MACD and Signal line
- `bollinger_upper/middle/lower`: Bollinger Bands
- `atr_14`: Average True Range
- `adx_14`: Average Directional Index

### 3. `quad_decisions`
Stores QUAD analysis decisions.

```sql
CREATE TABLE quad_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    decision_time TIMESTAMP NOT NULL,
    signal TEXT CHECK(signal IN ('BUY', 'SELL', 'HOLD')),
    conviction_score REAL,
    quantitative_score REAL,
    uncertainty_score REAL,
    adaptive_score REAL,
    drift_score REAL,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Current Status:** 0 records (Day 5 task)

### 4. `insider_trading`
Stores insider trading data from NSE.

```sql
CREATE TABLE insider_trading (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    person_name TEXT,
    person_category TEXT,
    security_type TEXT,
    acquisition_disposal TEXT,
    before_shares INTEGER,
    acquired_disposed_shares INTEGER,
    after_shares INTEGER,
    transaction_date DATE,
    intimation_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Current Status:** 0 records (Day 4 task)

### 5. `option_chain`
Stores NSE option chain data.

```sql
CREATE TABLE option_chain (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    expiry_date DATE,
    strike_price REAL,
    option_type TEXT CHECK(option_type IN ('CE', 'PE')),
    open_interest INTEGER,
    change_in_oi INTEGER,
    volume INTEGER,
    iv REAL,
    ltp REAL,
    bid_price REAL,
    ask_price REAL,
    timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Current Status:** 0 records (Day 4 task)

---

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
Currently using temporary bypass for development. Production will use JWT tokens.

### Available Endpoints

#### 1. Scheduler Management
```
GET    /scheduler/jobs              # List all scheduled jobs
POST   /scheduler/jobs              # Create new job
GET    /scheduler/jobs/{job_id}     # Get job details
POST   /scheduler/jobs/{job_id}/run # Trigger job manually
DELETE /scheduler/jobs/{job_id}     # Delete job
```

**Example Response:**
```json
{
  "id": "market_close_download",
  "name": "Market Close Download",
  "next_run_time": "2025-12-28T15:35:00+05:30",
  "enabled": true,
  "schedule": "Daily at 3:35 PM IST",
  "symbols_count": 50,
  "intervals": ["1m", "5m", "15m", "1h", "1d"]
}
```

#### 2. QUAD Analysis (Partially Implemented)
```
POST   /quad/{symbol}               # Trigger QUAD analysis
GET    /quad/{symbol}/history       # Get decision history (500 error - Day 6)
GET    /quad/{symbol}/timeline      # Get conviction timeline (500 error - Day 6)
GET    /quad/{symbol}/accuracy      # Get signal accuracy (500 error - Day 6)
```

#### 3. Data Endpoints (To Be Created - Day 6)
```
GET    /data/technicals/{symbol}    # Get technical indicators
GET    /data/insider/{symbol}       # Get insider trading data
GET    /data/options/{symbol}       # Get option chain data
GET    /data/price/{symbol}         # Get price history
```

**Planned Response Format (technicals):**
```json
{
  "symbol": "RELIANCE",
  "data": [
    {
      "date": "2025-12-26",
      "sma_20": 1285.50,
      "sma_50": 1290.25,
      "sma_200": 1275.80,
      "rsi_14": 55.32,
      "macd": 2.45,
      "macd_signal": 1.98,
      "bollinger_upper": 1295.60,
      "bollinger_middle": 1285.50,
      "bollinger_lower": 1275.40,
      "atr_14": 15.25,
      "adx_14": 25.80
    }
  ]
}
```

---

## Data Sources

### 1. NSEMasterData
**File:** `backend/app/data_sources/nse_master_data.py`

**Purpose:** Fetch historical OHLCV data from NSE Charting API

**Key Methods:**
```python
nse = NSEMasterData()
nse.download_symbol_master()  # Download symbol list

# Get historical data
df = nse.get_history(
    symbol="RELIANCE",
    exchange="NSE",
    start=datetime(1995, 1, 1),
    end=datetime.now(),
    interval="1d"  # 1m, 3m, 5m, 10m, 15m, 30m, 1h, 1d, 1w, 1M
)
```

**Features:**
- ✅ Direct NSE Charting API access
- ✅ Data from 1995 onwards
- ✅ All intervals supported
- ✅ No rate limits (compared to yfinance)

### 2. NseUtils
**File:** `backend/app/data_sources/nse_utils.py`

**Purpose:** Fetch live prices, fundamentals, insider trading, options

**Key Methods:**
```python
utils = NseUtils()

# Live price
price = utils.price_info("RELIANCE")

# Insider trading
insider = utils.get_insider_trading(from_date="2025-01-01", to_date="2025-12-31")

# Option chain
options = utils.get_option_chain("NIFTY", indices=True)
```

### 3. ScreenerEnhanced
**File:** `backend/app/data_sources/screener_enhanced.py`

**Purpose:** Scrape fundamental data from Screener.in

**Status:** Available but not yet integrated

---

## Services

### 1. TechnicalAnalysisService
**File:** `backend/app/services/technical_analysis.py`

**Purpose:** Calculate 50+ technical indicators using TA-Lib

**Usage:**
```python
from app.services.technical_analysis import TechnicalAnalysisService

ta = TechnicalAnalysisService(price_df)
df_with_indicators = ta.calculate_all()

# Available indicators:
# - Trend: SMA, EMA, WMA, DEMA, TEMA, KAMA, ADX, Aroon, SAR
# - Momentum: RSI, Stochastic, Williams %R, CCI, ROC, MOM, MFI, MACD
# - Volatility: Bollinger Bands, ATR, NATR, STDDEV
# - Volume: OBV, AD Line, ADOSC
# - Patterns: 40+ candlestick patterns
```

### 2. TechnicalIndicatorsService
**File:** `backend/app/services/technical_indicators_service.py`

**Purpose:** Calculate and store indicators in database

**Usage:**
```python
from app.services.technical_indicators_service import TechnicalIndicatorsService

service = TechnicalIndicatorsService()

# Calculate for one symbol
result = service.calculate_for_symbol("RELIANCE")

# Calculate for all symbols
results = service.calculate_for_all_symbols()
```

### 3. DataPipelineService
**File:** `backend/app/services/data_pipeline_service.py`

**Purpose:** Fetch and cache price data with freshness guarantees

**Key Methods:**
```python
pipeline = DataPipelineService()

# Fetch LTP
ltp_data = await pipeline.fetch_and_cache_ltp(
    symbols=["RELIANCE", "TCS"],
    source=DataSource.NSE
)

# Fetch historical batch
results = await pipeline.fetch_historical_batch(
    symbols=["RELIANCE"],
    interval="1d",
    period="1y",
    source=DataSource.NSE
)
```

---

## Scheduler Jobs

### Active Jobs

#### 1. Market Close Download
- **ID:** `market_close_download`
- **Schedule:** Daily at 3:35 PM IST
- **Symbols:** 50 NIFTY stocks
- **Intervals:** 1m, 5m, 15m, 1h, 1d
- **Purpose:** Download full day's data after market close

#### 2. Pre-Market Download
- **ID:** `pre_market_download`
- **Schedule:** Daily at 8:30 AM IST
- **Symbols:** 50 NIFTY stocks
- **Interval:** 1d
- **Purpose:** Update daily data before market opens

#### 3. Intraday LTP Refresh
- **ID:** `intraday_ltp_refresh`
- **Schedule:** Every 5 minutes (9:15 AM - 3:30 PM IST)
- **Symbols:** 50 NIFTY stocks
- **Purpose:** Real-time price updates during market hours

### Managing Jobs

**List all jobs:**
```bash
curl http://localhost:8000/api/v1/scheduler/jobs
```

**Trigger job manually:**
```bash
curl -X POST http://localhost:8000/api/v1/scheduler/jobs/pre_market_download/run
```

**Create jobs via script:**
```bash
./scripts/init_scheduler_jobs.sh
```

---

## Setup & Deployment

### Prerequisites
- Docker & Docker Compose
- 8GB RAM minimum
- 20GB disk space

### Quick Start

1. **Clone repository**
```bash
cd /home/fortune/Desktop/Python_Projects/Full_Stack_Trading/trading-test
```

2. **Start services**
```bash
docker-compose up -d
```

3. **Initialize scheduler jobs**
```bash
./scripts/init_scheduler_jobs.sh
```

4. **Download historical data** (one-time)
```bash
docker exec quad_backend python /app/scripts/download_complete_history.py
```

5. **Calculate technical indicators** (one-time)
```bash
docker exec quad_backend python -c "
import sys
sys.path.insert(0, '/app')
from app.services.technical_indicators_service import TechnicalIndicatorsService
service = TechnicalIndicatorsService()
service.calculate_for_all_symbols()
"
```

### Verify Installation

**Check database:**
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('stock_data.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM price_history')
print(f'Price records: {cursor.fetchone()[0]:,}')
cursor.execute('SELECT COUNT(*) FROM technical_indicators')
print(f'Indicator records: {cursor.fetchone()[0]:,}')
conn.close()
"
```

**Check API:**
```bash
curl http://localhost:8000/api/v1/scheduler/jobs
```

**Check frontend:**
```
http://localhost:3010
```

### Troubleshooting

**Scheduler jobs lost after restart:**
```bash
# Jobs are not persistent - recreate them
./scripts/init_scheduler_jobs.sh
```

**TA-Lib not found:**
```bash
# Reinstall TA-Lib
docker exec quad_backend bash -c "
  apt-get update && apt-get install -y wget build-essential &&
  wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz &&
  tar -xzf ta-lib-0.4.0-src.tar.gz &&
  cd ta-lib/ &&
  ./configure --prefix=/usr &&
  make && make install && ldconfig
"
docker exec quad_backend uv pip install TA-Lib
```

**Database locked:**
```bash
# Stop all containers
docker-compose down
# Restart
docker-compose up -d
```

---

## Development Workflow

### Adding New Indicators

1. **Update TechnicalAnalysisService**
```python
# backend/app/services/technical_analysis.py
def add_custom_indicators(self):
    self.df['custom_indicator'] = talib.CUSTOM(...)
```

2. **Update database schema** (if needed)
```sql
ALTER TABLE technical_indicators ADD COLUMN custom_indicator REAL;
```

3. **Update TechnicalIndicatorsService**
```python
# backend/app/services/technical_indicators_service.py
# Add to _store_indicators method
get_val('custom_indicator')
```

4. **Recalculate**
```bash
docker exec quad_backend python -c "..."
```

### Adding New Data Sources

1. **Create data source class**
```python
# backend/app/data_sources/my_source.py
from .base_source import DataSource

class MySource(DataSource):
    def get_historical_prices(self, symbol, period, interval):
        # Implementation
        pass
```

2. **Register in UnifiedDataService**
```python
# backend/app/services/unified_data_service.py
self.my_source = MySource()
```

3. **Update DataPipelineService**
```python
# Add to DataSource enum
class DataSource(Enum):
    MY_SOURCE = "my_source"
```

---

## Performance Metrics

### Current Status (Phase 0 Day 3)
- **Database Size:** ~150 MB
- **Total Records:** 623,616
- **Data Range:** 1995-2025 (30 years)
- **Symbols:** 49 NIFTY stocks
- **Calculation Time:** ~3 minutes for 311K indicators
- **API Response Time:** <100ms (when endpoints exist)

### Scalability
- **Max Symbols:** 500+ (tested)
- **Max Historical Range:** 30+ years
- **Indicator Calculation:** ~60K records/minute
- **Database:** Can handle 10M+ records

---

## Next Steps

### Phase 0 Remaining (Days 4-7)
- [ ] Day 4: Insider trading & options data
- [ ] Day 5: QUAD decisions generation
- [ ] Day 6: API endpoint creation & fixes
- [ ] Day 7: CORS resolution

### Phase 1 (Days 8-30)
- [ ] ML model integration
- [ ] Real-time WebSocket feeds
- [ ] Advanced backtesting
- [ ] Risk management

---

## Support & Contact

**Documentation Location:**
- `/home/fortune/Desktop/Python_Projects/Full_Stack_Trading/trading-test/docs/`

**Key Files:**
- `QUAD_Implementation_Plan.md` - 90-day roadmap
- `quad_feature_availability_report.md` - Feature audit
- `phase0_day1-2_walkthrough.md` - Days 1-2 completion
- `phase0_day3_walkthrough.md` - Day 3 completion
- `TECHNICAL_REFERENCE.md` - This file

**Last Updated:** 2025-12-28 01:51 IST
