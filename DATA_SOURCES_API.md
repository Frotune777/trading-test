# API Level Analysis of Data Sources

This document provides a technical "API Level" breakdown of the **FOUR** core data source modules: `ScreenerEnhanced`, `NSEComplete`, `NseUtils`, and `NSEMasterData`.

---

## 1. Screener Enhanced (`screener_enhanced.py`)
**Type**: Web Scraper (HTML Parsing)
**Target**: `screener.in`

### Primary Public API
| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_complete_data(symbol)` | `Dict[str, Any]` | **Main Entry Point.** Fetches *everything*: metrics, financial tables (Q&A, BS, CF, P&L), and peer comparisons. |
| `get_company_info(symbol)` | `Dict` | Returns basic company info (Name, Industry, Website, Description). |
| `get_price_data(symbol)` | `Dict` | Returns simple price info (Current, High, Low) derived from metrics. |
| `get_historical_prices(...)` | `DataFrame` | *Not fully implemented.* Returns empty DataFrame (Screener.in is not a historical price source). |

### Internal Mechanisms
- **Extraction**: Uses `BeautifulSoup` to parse key-value pairs from list items (`#top-ratios`) and tables (`.data-table`).
- **Peers**: Makes a separate AJAX call to `/api/company/{warehouse_id}/peers/` to get peer data.
- **Data Types**: Key metrics are parsed into floats/ints. Financial tables are converted to **Pandas DataFrames**.

---

## 2. NSE Complete (`nse_complete_ORIGINAL.py`)
**Type**: Aggregator / Facade
**Target**: Wrapper around `NseUtils` and `NSEMasterData` (yfinance/charting)

### Primary Public API
| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_complete_data(symbol)` | `Dict` | **Main Entry Point.** Aggregates company info, price, historicals, and intraday data into one object. |
| `get_company_info(symbol)` | `Dict` | Delegates to `NseUtils.equity_info`. |
| `get_price_data(symbol)` | `Dict` | Delegates to `NseUtils.price_info` + `NseUtils.get_52week_high_low`. |
| `get_historical_prices(...)` | `DataFrame` | Delegates to `NSEMasterData` (uses `yfinance` history). |
| `get_futures_data(...)` | `DataFrame` | Fetches historical *Futures* data via `NSEMasterData`. |
| `get_options_data(...)` | `DataFrame` | Fetches historical *Options* data via `NSEMasterData`. |
| `get_option_chain(...)` | `DataFrame` | Delegates to `NseUtils.get_option_chain`. |
| `get_corporate_actions` | `DataFrame` | Delegates to `NseUtils.get_corporate_action`. |
| `get_bulk_deals(...)` | `DataFrame` | Delegates to `NseUtils.get_bulk_deals`. |
| `get_insider_trading(...)` | `DataFrame` | Delegates to `NseUtils.get_insider_trading`. |

### Key Characteristics
- **No Direct Fetching**: acts mostly as a high-level organizer.
- **Hybrid Source**: Combines live NSE data (via `NseUtils`) with stable historical data (via `NSEMasterData`/Yahoo).

---

## 3. Nse Utils (`nse_utils.py`)
**Type**: Low-Level HTTP Client
**Target**: `nseindia.com` (Main Website API)

### Core Capabilities (Direct API Wrappers)

**1. Live Market Data**
- `price_info(symbol)`: Returns live price snapshot (LTP, %Change, VWAP).
- `equity_info(symbol)`: Full meta-data (Listing date, ISIN, Sector, Industry) + Order Book.
- `get_market_depth(symbol)`: Returns top 5 Bid/Ask.
- `pre_market_info(category)`: Pre-open market data.
- `get_gainers_losers()`: Top gainers/losers for Nifty, BankNifty, FNO, etc.
- `get_advance_decline()`: Market breadth (Advances/Declines).
- `most_active_*()`: Methods for most active stocks/contracts by volume/value.

**2. Derivatives (F&O)**
- `get_option_chain(symbol)`: Returns full Option Chain (CE/PE, OI, IV, Greeks) as a **DataFrame**.
- `get_live_option_chain(...)`: More granular live chain data.
- `futures_data(symbol)`: List of available futures contracts.

**3. Historical & Reports**
- `get_52week_high_low()`: Downloads CSV from NSE Archives.
- `get_index_historic_data(...)`: Historical index levels.
- `fno_bhav_copy(...)`: Downloads and unzips daily F&O Bhavcopy.
- `bhav_copy_with_delivery(...)`: Downloads capital market Bhavcopy with delivery stats.

**4. Corporate & Macro**
- `fii_dii_activity()`: Daily institutional trading stats.
- `get_corporate_action(...)`: Ex-dates, Record dates for Dividends/Splits.
- `get_corporate_announcement(...)`: Board meeting outcomes, press releases.
- `get_insider_trading(...)`: **Significant Insider Trading (SAST/PIT) data.**
- `get_bulk_deals(...)` / `get_block_deals(...)`: Large trade data.
- `get_short_selling(...)`: Daily short selling reports.
- `get_index_pe_ratio / pb_ratio`: Market valuation ratios.
- `is_nse_trading_holiday`: Utility to check market holidays.

### Internal Mechanisms
- **Session Management**: Maintains a `requests.Session` with headers mimicking a real browser (`User-Agent`, `Upgrade-Insecure-Requests`).
- **Cookies**: Visits `nseindia.com` home page first to initialize valid cookies before hitting API endpoints.

---

## 4. NSE Master Data (`nse_master_data.py`)
**Type**: Charting API Client
**Target**: `charting.nseindia.com`

### Core Capabilities
This module bypasses the main website and hits the lightweight charting endpoints.

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_history(symbol, ...)` | `DataFrame` | **Reliable Historical Data.** Fetches OHLCV data for ANY timeframe (1m, 5m, 15m, 1h, 1d). |
| `search(symbol)` | `DataFrame` | Searches for symbols in NSE/NFO database. |
| `download_symbol_master()` | `None` | Downloads the full list of active NSE and NFO symbols (ScripCode mapping). |
| `get_nse_symbol_master()` | `DataFrame` | Raw download of the master pipe-separated file. |

### Key Characteristics
- **Fast & Lightweight**: Uses `charting.nseindia.com` which is faster than the main site.
- **Intraday Granularity**: The ONLY source for 1-minute to 60-minute historical intraday data.
- **ScripCode Mapping**: Maintains the mapping between Symbol (e.g., 'TCS') and ScripCode (e.g., '12345') required for charting APIs.
