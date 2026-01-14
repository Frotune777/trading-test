# Project Data Sources Documentation

This document outlines the data sources available in the `quad_trading` project, specifically within `backend/app/data_sources/nse_utils.py`.

## 1. Equity & Market Status
- **Equity Info**: `equity_info(symbol)` (✅ Active - NextApi)
- **Top Gainers/Losers**: `get_gainers_losers()` (✅ Active)
- **Advance/Decline**: `get_advance_decline()` (✅ Active)
- **Index Ratios**: `get_index_pe_ratio()`, `get_index_pb_ratio()`, `get_index_div_yield()` (✅ Active)

## 2. Historical & Periodic Data
- **Method**: `get_historical_data(symbol, from_date, to_date)`
- **Source**: NSE India Chart API (Fallback)
- **Endpoint**: `https://www.nseindia.com/api/chart-databyindex?index={symbol}`
- **Status**: ✅ **Active** (Fallback implementation)
- **Details**: Fetches timestamped price data for periodic analysis (52-week High/Low).

## 3. Derivatives & Option Chain
- **Option Chain**: `get_option_chain(symbol)` (✅ **Fixed**)
    - *Status*: Working. Requires visiting the Option Chain page to initialize session cookies, which is now handled automatically.
- **Most Active Derivatives**: (✅ Active)
    - `most_active_index_calls()`, `most_active_index_puts()`
    - `most_active_stock_calls()`, `most_active_stock_puts()`
    - `most_active_contracts_by_oi()`, `most_active_contracts_by_volume()`

## 4. Corporate & Insider
- **Corporate Actions**: `get_corporate_action()` (✅ Active)
- **Insider Trading**: `get_insider_trading()` (✅ Active)
- **Most Active Equities**: `most_active_equity_stocks_by_volume()` (✅ Active)

## 5. Other
- **Bulk/Block Deals**: `get_bulk_deals()`, `get_block_deals()` (Untested but likely active)
- **ETF List**: `get_etf_list()` (Untested)

## File References
- **Script**: `backend/app/data_sources/nse_utils.py`
- **Verification**: `backend/verify_all_sources.py`, `backend/verify_corporate_insider.py`
