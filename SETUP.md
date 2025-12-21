# Trading System - Setup Guide

## Quick Start

### 1. Activate Virtual Environment

```bash
cd /home/zohra/Documents/Stock_analysis/trading-test
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note**: If `TA-Lib` installation fails, you can comment it out in `requirements.txt` and install it separately later.

### 3. Verify Installation

Test that imports work correctly:

```bash
python3 -c "from backend.app.database.db_manager import DatabaseManager; print('✓ Database module OK')"
python3 -c "from backend.app.data_sources.nse_complete import NSEComplete; print('✓ Data sources OK')"
python3 -c "from backend.app.services.data_aggregator import HybridAggregator; print('✓ Services OK')"
```

### 4. Run the Application

#### Option A: Streamlit Dashboard
```bash
streamlit run frontend/app.py
```

#### Option B: FastAPI Backend
```bash
cd backend
uvicorn app.main:app --reload
```

#### Option C: Utility Scripts
```bash
# Update database
python3 scripts/update_db.py --help

# Export data
python3 scripts/export_data.py
```

---

## Project Structure

```
trading-test/
├── backend/app/          # Core logic
│   ├── database/         # Database management
│   ├── data_sources/     # Data fetching (NSE, Yahoo, Screener)
│   ├── services/         # Business logic
│   ├── ml/              # Machine learning
│   └── core/            # Utilities (cache, rate limiter)
├── frontend/            # Streamlit UI
├── scripts/             # Utility scripts
├── venv/               # Virtual environment (do not commit)
└── requirements.txt     # Dependencies
```

---

## Deactivating Virtual Environment

When you're done working:

```bash
deactivate
```

---

## Troubleshooting

### Virtual Environment Not Found
```bash
python3 -m venv venv
source venv/bin/activate
```

### Permission Denied on setup_env.sh
```bash
chmod +x setup_env.sh
./setup_env.sh
```

### TA-Lib Installation Issues
If TA-Lib fails to install:
1. Comment it out in `requirements.txt`
2. Install system dependencies first:
   ```bash
   sudo apt-get install ta-lib  # Ubuntu/Debian
   # or
   brew install ta-lib          # macOS
   ```
3. Then install the Python wrapper:
   ```bash
   pip install TA-Lib
   ```

### Module Not Found Errors
Make sure:
1. Virtual environment is activated: `source venv/bin/activate`
2. You're in the project root directory
3. Dependencies are installed: `pip install -r requirements.txt`

---

## Environment Variables

Create a `.env` file in the project root if needed:

```bash
# Database
DATABASE_URL=sqlite:///stock_data.db

# API Keys (if required)
# NSE_API_KEY=your_key_here
# YAHOO_API_KEY=your_key_here

# Redis (if using)
# REDIS_HOST=localhost
# REDIS_PORT=6379
```

---

## Daily Workflow

```bash
# 1. Navigate to project
cd /home/zohra/Documents/Stock_analysis/trading-test

# 2. Activate virtual environment
source venv/bin/activate

# 3. Work on your project
streamlit run frontend/app.py
# or
python3 scripts/update_db.py TCS INFY

# 4. When done
deactivate
```
