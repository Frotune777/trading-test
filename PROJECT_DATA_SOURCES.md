# Project Data Sources Documentation

This document outlines the data sources available in the `quad_trading` project, specifically within `backend/app/data_sources/nse_utils.py`.

## 1. Equity Data
- **Method**: `equity_info(symbol)`
- **Source**: NSE India Website (NextApi)
- **Endpoint**: `https://www.nseindia.com/api/NextApi/apiClient/GetQuoteApi`
- **Status**: ✅ **Active** (Using NextApi as of Jan 2026)
- **Details**: Fetches live price, OHLC, volume, and metadata. Response is polyfilled to match legacy schema (e.g., `priceInfo` maps to `tradeInfo`/`metaData`).

## 2. Historical & Periodic Data
- **Method**: `get_historical_data(symbol, from_date, to_date)`
- **Source**: NSE India Chart API
- **Endpoint**: `https://www.nseindia.com/api/chart-databyindex?index={symbol}`
- **Status**: ✅ **Active** (Fallback implementation)
- **Details**: The official historical API is restricted. We use the Chart API to retrieve timestamped price data (Intraday/Daily depending on NSE's feed). This serves as the source for periodic data analysis.

## 3. Corporate Actions
- **Method**: `get_corporate_action()`
- **Source**: NSE India Corporate Filings
- **Endpoint**: `https://www.nseindia.com/api/corporates-corporateActions`
- **Status**: ✅ **Active**
- **Details**: Fetches Dividends, Splits, Bonus, etc. Verified working.

## 4. Insider Trading
- **Method**: `get_insider_trading()`
- **Source**: NSE India Insider Trading Filings
- **Endpoint**: `https://www.nseindia.com/api/corporates-pit`
- **Status**: ✅ **Active**
- **Details**: Fetches insider acquisition/disposal data. Verified working.

## 5. Option Chain (Equity)
- **Method**: `get_option_chain(symbol)`
- **Source**: NSE India Option Chain API
- **Endpoint**: `https://www.nseindia.com/api/option-chain-equities`
- **Status**: ⚠️ **Partial/Unstable**
- **Details**: Currently returns empty data consistently. Likely requires a specific `NextApi` endpoint or improved session flow similar to Equity.

## File References
- **Script**: `backend/app/data_sources/nse_utils.py`
- **Verification Scripts**:
    - `backend/verify_nse_scrape.py` (Equity/Option Chain)
    - `backend/verify_corporate_insider.py` (Corporate/Insider)
