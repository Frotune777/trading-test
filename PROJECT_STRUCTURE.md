# fortune_trading

**Path:** `/home/fortune/Desktop/Python_Projects/fortune_trading`  
**Analyzed:** 2025-11-10 14:17

## Summary

- **Files:** 103
- **Lines:** 24,248
- **Dependencies:** abc, argparse, ast, base_source, bs4, cache_manager, collections, concurrent, config, core, csv, dashboard, data_sources, database, datetime, db_manager, examples, hashlib, io, json, logging, nse_complete, nse_master_data, nse_utils, numpy, os, pandas, pathlib, pickle, plotly, rate_limiter, re, requests, schema, shutil, sqlite3, streamlit, structure, subprocess, sys, tempfile, tests, threading, time, tkinter, traceback, typing, unified_exporter, unittest, updater, validate_data, yfinance, zipfile

## Structure


### `./`

#### Refactoring.py (714 lines)

**Imports:** `ast, datetime, os, pathlib, re, shutil, subprocess, sys, typing`

```python
class NSERefactoringTool  # Automated refactoring tool for NSE consolidation
    __init__(self, project_root:str=None)
    log(self, message:str, level:str='INFO')  # Log message to file and console
    create_backup(self)  # Create backup of all files to be modified
    create_rollback_script(self)  # Create a script to rollback changes if needed
    analyze_dependencies(self)  # Find all files that import NSE modules
    extract_methods(self, file_path:Path)  # Extract all methods from a Python file
    merge_nse_files(self)  # Merge nse_utils.py and nse_master_data.py into nse_complete.
    generate_consolidated_nse_complete(self, current, utils_content, master_content, utils_methods, master_methods)  # Generate the consolidated nse_complete.py content
    extract_imports(self, content:str)  # Extract import statements from Python code
    convert_to_class_method(self, function_code:str)  # Convert standalone function to class method
    ensure_proper_indentation(self, code:str)  # Ensure code has proper class method indentation
    validate_python_syntax(self, file_path:Path)  # Validate Python file syntax
    update_imports(self, new_nse_complete:Path)  # Update import statements in all dependent files
    run_tests(self)  # Run tests to verify refactoring didn't break anything
    finalize_refactoring(self, new_nse_complete:Path)  # Finalize refactoring by replacing old file and cleaning up
    generate_report(self)  # Generate final refactoring report
    run(self, skip_tests:bool=False)  # Run complete refactoring process
def main()  # Main entry point
```

#### auto_fix_tests.py (73 lines)

**Imports:** `pathlib, re`

```python
def replace_in_file(path, replacements)
def main()
```

#### auto_fix_tests_v2.py (90 lines)

**Imports:** `pathlib, re`

```python
def replace_in_file(path:Path, replacements)
def main()
```

#### auto_fix_tests_v4.py (109 lines)

**Imports:** `pathlib, re, subprocess`

```python
def replace_in_file(path:Path, replacements)
def patch_tests()
def run_tests()
```


### `backups/refactor_20251028_001034/`

#### nse_complete.py (258 lines)

**Imports:** `base_source, datetime, logging, nse_master_data, nse_utils, pandas, pathlib, sys, typing`

```python
class NSEComplete(DataSource)  # Complete NSE data source using:
    __init__(self)
    get_company_info(self, symbol:str)  # Get company information.
    get_price_data(self, symbol:str)  # Get current price data.
    get_historical_prices(self, symbol:str, period:str='1y', interval:str='1d')  # Get historical OHLCV data.
    get_intraday_data(self, symbol:str, interval:str='5m')  # Get today's intraday data.
    get_futures_data(self, symbol:str, expiry:str=None, period:str='1m', interval:str='1d')  # Get futures historical data.
    get_options_data(self, symbol:str, strike:int, option_type:str, expiry:str=None, interval:str='5m')  # Get options historical data.
    get_option_chain(self, symbol:str, indices:bool=True)  # Get full option chain.
    get_market_depth(self, symbol:str)  # Get bid/ask depth.
    get_corporate_actions(self, from_date:str=None, to_date:str=None, filter:str=None)  # Get corporate actions.
    get_bulk_deals(self, from_date:str=None, to_date:str=None)  # Get bulk deals.
    get_insider_trading(self, from_date:str=None, to_date:str=None)  # Get insider trading data.
    get_complete_data(self, symbol:str)  # Get complete dataset for a symbol.
```

#### nse_master_data.py (306 lines)

**Imports:** `datetime, json, pandas, re, requests, time`

```python
class NSEMasterData
    __init__(self)
    search(self, symbol, exchange, match=False)  # Search for symbols in the specified exchange.
    get_nse_symbol_master(self, url)
    download_symbol_master(self)  # Download NSE and NFO master data.
    search_symbol(self, symbol, exchange)  # Search for a symbol in the specified exchange and return the
    get_history(self, symbol='Nifty 50', exchange='NSE', start=None, end=None, interval='1d')  # Get historical data for a symbol.
```

#### nse_utils.py (1185 lines)

**Imports:** `datetime, io, pandas, requests, zipfile`

```python
class NseUtils
    __init__(self)
    pre_market_info(self, category='All')
    get_index_details(self, category, list_only=False)
    clearing_holidays(self, list_only=False)  # Returns the list of NSE clearing holidays
    trading_holidays(self, list_only=False)  # Returns the list of NSE trading holidays
    is_nse_trading_holiday(self, date_str=None)  # Return True if the date supplied in a NSE trading holiday, e
    is_nse_clearing_holiday(self, date_str=None)  # Return True if the date supplied in a NSE clearing holiday, 
    equity_info(self, symbol)  # Extracts the full details of a symbol as see on NSE website
    price_info(self, symbol)  # Gets all key price related information for a given stock
    futures_data(self, symbol, indices=False)  # Returns the list of futures instruments for a given stock an
    get_option_chain(self, symbol, indices=False)  # Returns the full option chain table as seen on NSE website f
    get_52week_high_low(self, stock=None)  # Get 52 Week High and Low data.  If stock is provided, the Hi
    fno_bhav_copy(self, trade_date:str='')  # Get the NSE FNO bhav copy data as per the traded date
    bhav_copy_with_delivery(self, trade_date:str)  # Get the NSE bhav copy with delivery data as per the traded d
    equity_bhav_copy(self, trade_date:str)  # Extract Equity Bhav Copy per the traded date provided
    bhav_copy_indices(self, trade_date:str)  # Get nse bhav copy as per the traded date provided
    fii_dii_activity(self)  # FII and DII trading activity of the day in data frame
    get_live_option_chain(self, symbol:str, expiry_date:str=None, oi_mode:str='full', indices=False)  # get live nse option chain.
    get_market_depth(self, symbol)  # Function to retrieve market depth for a given symbol
    get_index_historic_data(self, index:str, from_date:str=None, to_date:str=None)  # get historical index data set for the specific time period.
    get_index_data(self, index:str, from_date:str, to_date:str)
    get_equity_full_list(self, list_only=False)  # get list of all equity available to trade in NSE
    get_fno_full_list(self, list_only=False)  # get a dataframe of all listed derivative list with the recen
    get_gainers_losers(self)
    get_corporate_action(self, from_date_str:str=None, to_date_str:str=None, filter:str=None)
    get_corporate_announcement(self, from_date_str:str=None, to_date_str:str=None)
    get_index_pe_ratio(self)
    get_index_pb_ratio(self)
    get_index_div_yield(self)
    get_advance_decline(self)
    most_active_equity_stocks_by_volume(self)
    most_active_equity_stocks_by_value(self)
    most_active_index_calls(self)
    most_active_index_puts(self)
    most_active_stock_calls(self)
    most_active_stock_puts(self)
    most_active_contracts_by_oi(self)
    most_active_contracts_by_volume(self)
    most_active_futures_contracts_by_volume(self)
    most_active_options_contracts_by_volume(self)
    get_insider_trading(self, from_date:str=None, to_date:str=None)
    get_upcoming_results_calendar(self)
    get_etf_list(self)
    get_bulk_deals(self, from_date:str=None, to_date:str=None)
    get_block_deals(self, from_date:str=None, to_date:str=None)
    get_short_selling(self, from_date:str=None, to_date:str=None)
```


### `backups/refactor_20251028_001402/`

#### nse_complete.py (1425 lines)

**Imports:** `base_source, data_sources, datetime, io, json, logging, pandas, pathlib, re, requests, sys, time, typing, zipfile`

```python
class NSEComplete(DataSource)  # Complete NSE data source with all functionality consolidated
    __init__(self)
    _initialize_session(self)  # Initialize session with NSE cookies
    get_complete_data(self, symbol:str)  # Get complete dataset for a symbol.
```


### `backups/refactor_20251028_001446/`

#### nse_complete.py (1425 lines)

**Imports:** `base_source, data_sources, datetime, io, json, logging, pandas, pathlib, re, requests, sys, time, typing, zipfile`

```python
class NSEComplete(DataSource)  # Complete NSE data source with all functionality consolidated
    __init__(self)
    _initialize_session(self)  # Initialize session with NSE cookies
    get_complete_data(self, symbol:str)  # Get complete dataset for a symbol.
```


### `./`

#### config.py (60 lines)

**Imports:** `datetime, pathlib`


### `core/`

#### __init__.py (8 lines)

**Imports:** `cache_manager, rate_limiter`

#### cache_manager.py (131 lines)

**Imports:** `datetime, hashlib, logging, pathlib, pickle, typing`

```python
class CacheManager  # Multi-layer cache system with TTL.
    __init__(self, enabled:bool=True, cache_dir:str='.cache')
    _get_cache_key(self, key:str)  # Generate safe cache key.
    _get_cache_file(self, key:str)  # Get cache file path.
    get(self, key:str)  # Get cached value.
    set(self, key:str, value:Any, ttl:int=3600)  # Set cache value with TTL.
    clear(self)  # Clear all cache.
    get_stats(self)  # Get cache statistics.
```

#### data_merger.py (102 lines)

**Imports:** `logging, pandas, typing`

```python
class DataMerger  # Intelligent data merging with conflict resolution.
    merge_price_data(sources:List[Dict[str, Any]], priority:List[str])  # Merge price data from multiple sources.
    validate_price_data(data:Dict[str, Any])  # Validate and clean price data.
class DataQualityChecker  # Check data quality and completeness.
    assess_quality(data:Dict[str, Any])  # Assess overall data quality.
    _get_grade(score:float)  # Convert score to letter grade.
```

#### hybrid_aggregator.py (402 lines)

**Imports:** `concurrent, config, core, data_sources, datetime, logging, pandas, pathlib, sys, typing`

```python
class HybridAggregator  # Intelligent data aggregator combining multiple sources.
    __init__(self, use_cache:bool=True)
    _test_sources(self)  # Test all data sources.
    get_stock_data(self, symbol:str, include_historical:bool=True)  # Get comprehensive stock data from NSE and Yahoo.
    get_fundamental_data(self, symbol:str)  # Get comprehensive fundamental data from Screener.
    get_complete_analysis(self, symbol:str)  # Get EVERYTHING: NSE price data + Screener fundamentals + Yah
    _fetch_from_source(self, symbol:str, source_name:str)  # Fetch all available data from a single source.
    _merge_data(self, symbol:str, raw_data:Dict)  # Intelligently merge data from multiple sources.
    _merge_company_info(self, raw_data:Dict)  # Merge company information from all sources.
    _merge_price_data(self, raw_data:Dict)  # Merge price data with priority.
    _select_best_historical(self, raw_data:Dict)  # Select best historical data.
    get_quick_quote(self, symbol:str)  # Get only price data (fast).
    batch_fetch(self, symbols:List[str], max_workers:int=5)  # Fetch data for multiple symbols in parallel.
```

#### model_data_prep.py (652 lines)

**Imports:** `datetime, logging, numpy, pandas, typing`

```python
class ModelDataPrep  # Prepare data for financial models
    __init__(self, nse, db)
    prepare_price_prediction_data(self, symbol:str, lookback_days:int=365)  # Prepare data for price prediction models (LSTM, ARIMA, etc.)
    prepare_volatility_model_data(self, symbol:str, lookback_days:int=180)  # Prepare data for volatility models (GARCH, Stochastic Vol, e
    prepare_sentiment_data(self, symbol:str, lookback_days:int=90)  # Prepare data for sentiment analysis
    prepare_portfolio_data(self, symbols:List[str], lookback_days:int=365)  # Prepare data for portfolio optimization (Markowitz, Black-Li
    prepare_options_trading_data(self, symbol:str, expiry:Optional[str]=None)  # Prepare data for options trading strategies
    prepare_event_driven_data(self, symbol:str, lookback_days:int=180)  # Prepare data for event-driven strategies
    _calculate_quality_score(self, quality_dict:Dict)  # Calculate overall data quality score
    export_for_talib(self, price_history:pd.DataFrame)  # Export price data in format ready for TA-Lib
```

#### mtf_manager.py (571 lines)

**Imports:** `datetime, logging, numpy, pandas, pathlib, sqlite3, typing`

```python
class TimeFrame  # Timeframe definitions and conversions
    get_minutes(cls, timeframe:str)  # Get minutes for a timeframe
    get_higher_timeframe(cls, timeframe:str)  # Get the next higher timeframe
    get_lower_timeframe(cls, timeframe:str)  # Get the next lower timeframe
class MTFDataManager  # Multi-Timeframe Data Manager
    __init__(self, db_manager, nse_source)
    get_mtf_data(self, symbol:str, timeframes:List[str], lookback_days:int=30)  # Get data for multiple timeframes
    _get_timeframe_data(self, symbol:str, timeframe:str, lookback_days:int)  # Get data for a specific timeframe
    _get_daily_plus_data(self, symbol:str, timeframe:str, lookback_days:int)  # Get daily, weekly, or monthly data
    _get_intraday_data(self, symbol:str, timeframe:str, lookback_days:int)  # Get intraday data (1m, 5m, 15m, 30m, 1h, 4h)
    _fetch_from_nse(self, symbol:str, interval:str, lookback_days:int)  # Fetch intraday data from NSE
    _get_intraday_from_db(self, symbol:str, timeframe:str, lookback_days:int)  # Get intraday data from database
    _save_intraday_to_db(self, symbol:str, timeframe:str, df:pd.DataFrame)  # Save intraday data to database
    _resample_ohlcv(self, df:pd.DataFrame, rule:str)  # Resample OHLCV data to higher timeframe
    _resample_to_timeframe(self, df:pd.DataFrame, target_timeframe:str)  # Resample to specific timeframe
    align_mtf_data(self, mtf_data:Dict[str, pd.DataFrame], reference_tf:str='1d')  # Align multiple timeframes to same datetime index
    get_htf_value_at_ltf(self, htf_data:pd.DataFrame, ltf_timestamp:datetime, column:str='close')  # Get higher timeframe value at a lower timeframe timestamp
    calculate_mtf_trend(self, mtf_data:Dict[str, pd.DataFrame], ma_period:int=20)  # Calculate trend direction for each timeframe
    is_mtf_aligned(self, mtf_data:Dict[str, pd.DataFrame], direction:str='UP', min_timeframes:int=3)  # Check if multiple timeframes are aligned in same direction
    validate_mtf_data(self, mtf_data:Dict[str, pd.DataFrame])  # Validate data quality across timeframes
```

#### rate_limiter.py (43 lines)

**Imports:** `collections, logging, threading, time`

```python
class RateLimiter  # Token bucket rate limiter.
    __init__(self, calls_per_minute:int=30)
    wait_if_needed(self)  # Wait if rate limit would be exceeded.
```


### `dashboard/`

#### __init__.py (3 lines)

#### app.py (1315 lines)

**Imports:** `data_sources, database, datetime, io, pandas, pathlib, plotly, sqlite3, streamlit, sys`

```python
def get_database()  # Get database connection (cached).
def get_updater()  # Get data updater (cached).
def get_nse()  # Get NSE data source (cached).
def validate_nse_symbol(symbol:str)  # Validate if symbol exists in NSE.
def download_historical_data(symbol:str, period:str, interval:str)  # Download historical data from NSE.
def download_intraday_data(symbol:str, interval:str)  # Download intraday data from NSE.
def convert_df_to_csv(df)  # Convert DataFrame to CSV.
def convert_df_to_excel(df)  # Convert DataFrame to Excel.
def get_all_suggestions()  # Get all popular stocks as flat list.
def execute_sql_query(query:str, db_path:str=None)  # Execute SQL query and return results.
```

#### app_v3.py (422 lines)

**Imports:** `dashboard, datetime, pathlib, streamlit, sys`

```python
def initialize_session_state()  # Initialize all session state variables
def placeholder_page(page_name:str)  # Placeholder page when actual page fails to load
def render_system_status()  # Render system status indicators in sidebar
def main()  # Main application entry point
def render_footer()  # Render application footer
```

#### app_v3_copy.py (454 lines)

**Imports:** `dashboard, datetime, pathlib, streamlit, sys, time`

```python
def get_dashboard_statistics()  # Fetches table statistics from the database.
def initialize_session_state()  # Initialize all session state variables and fetch initial dat
def render_system_status()  # Render system status indicators in sidebar
def main()  # Main application entry point
def placeholder_page(page_name:str)  # Placeholder page when actual page fails to load
def render_footer()  # Render application footer
```


### `dashboard/components/`

#### charts.py (128 lines)

**Imports:** `dashboard, pandas, plotly, streamlit`

```python
def render_price_chart(price_history:pd.DataFrame, symbol:str)  # Render price and volume charts
def render_shareholding_chart(shareholding:pd.DataFrame)  # Render shareholding pie chart
```

#### metrics.py (43 lines)

**Imports:** `dashboard, pandas, streamlit`

```python
def render_metrics_row(metrics:dict)  # Render key metrics in a row
```

#### navigation.py (62 lines)

**Imports:** `streamlit`

```python
def render_navigation()  # Render top navigation bar
```

#### tables.py (73 lines)

**Imports:** `dashboard, pandas, streamlit`

```python
def render_period_summary(snapshot:dict, last_update)  # Render period summary table
def render_quarterly_results(quarterly:pd.DataFrame)  # Render quarterly results table
def render_peer_comparison(peers:pd.DataFrame)  # Render peer comparison table
```


### `dashboard/`

#### config.py (362 lines)

**Imports:** `os, pathlib`


### `dashboard/pages/`

#### analytics.py (346 lines)

**Imports:** `dashboard, datetime, numpy, pandas, plotly, streamlit`

```python
def analytics_page()  # Main analytics dashboard with price trends
def render_price_trend_chart(price_history:pd.DataFrame, symbol:str)  # Render comprehensive price trend analysis
```

#### data_manager.py (831 lines)

**Imports:** `dashboard, datetime, logging, pandas, streamlit, time, typing`

```python
def render_html_table(df:pd.DataFrame, height:int=None)  # Render DataFrame as HTML table with dark theme
def validate_stock_symbol(symbol:str, nse)  # Validate if stock symbol exists on NSE
def batch_validate_symbols(symbols:List[str], nse)  # Validate multiple symbols
def get_safe_update_summary(db)  # Safely retrieve update summary
def get_sector_statistics(db)  # Get sector counts
def get_data_freshness_distribution(db, companies:List[Dict])  # Calculate freshness
def data_manager_page()  # Main data management dashboard
def add_new_stock_tab(db, updater, nse)  # Add new stocks with validation
def add_and_download_stocks(symbols:List[str], existing:List[str], db, updater)  # Add validated stocks and download their data
def download_data_tab(db, updater)  # Bulk download interface
def update_database_tab(db, updater)  # Update operations
def database_stats_tab(db)  # Statistics
def update_log_tab(db)  # Update log
def download_stocks(symbols, force, delay, updater)  # Batch download
def update_all_stocks(companies, updater)
def update_stale_stocks(hours, updater)
def show_summary(results)  # Show summary
```

#### database_explorer.py (552 lines)

**Imports:** `datetime, json, pandas, pathlib, sqlite3, streamlit`

```python
def database_explorer_page()  # Database Explorer - Browse tables and run SQL queries
def browse_tables_tab(conn)  # Browse database tables
def display_table_data(conn, table_name)  # Display data from a selected table
def sql_query_tab(conn)  # SQL Query executor
def schema_viewer_tab(conn)  # View database schema
def quick_stats_tab(conn)  # Quick database statistics
```

#### models.py (416 lines)

**Imports:** `core, dashboard, datetime, json, pandas, streamlit`

```python
def models_page()  # Financial models configuration and data export
def price_prediction_tab(model_prep, db)  # Price prediction model configuration
def volatility_models_tab(model_prep, db)  # Volatility modeling configuration
def sentiment_analysis_tab(model_prep, db)  # Sentiment analysis configuration
def event_driven_tab(model_prep, db)  # Event-driven strategy configuration
def portfolio_optimization_tab(model_prep, db)  # Portfolio optimization configuration
def options_trading_tab(model_prep, db)  # Options trading configuration
def display_model_data(data:dict, model_type:str)  # Display prepared model data with quality assessment
```

#### mtf_analysis.py (273 lines)

**Imports:** `core, dashboard, datetime, pandas, plotly, streamlit`

```python
def mtf_analysis_page()  # Multi-Timeframe Analysis Dashboard
def display_mtf_analysis(mtf_data:dict, symbol:str, chart_type:str, mtf_manager:MTFDataManager)  # Display comprehensive MTF analysis
def render_timeframe_chart(df:pd.DataFrame, symbol:str, timeframe:str, chart_type:str, trend:str)  # Render chart for single timeframe
```

#### portfolio.py (38 lines)

**Imports:** `pandas, plotly, streamlit`

```python
def portfolio_page()  # Portfolio management
```

#### research.py (229 lines)

**Imports:** `core, dashboard, datetime, pandas, re, streamlit, time, typing`

```python
def research_page()  # Research and screening dashboard
def screener_tab()  # Stock screener
def run_screener(symbols:List[str], min_roe:float, max_pe:float, min_roce:float, min_div_yield:float)  # Execute screening
def sector_analysis_tab()  # Sector analysis
def custom_research_tab()  # Custom tools
def compare_stocks(symbols:List[str])  # Compare stocks
def extract_number(value:str)  # Extract number from string
```

#### settings.py (365 lines)

**Imports:** `dashboard, datetime, pathlib, shutil, streamlit`

```python
def settings_page()  # Application settings and configuration
def general_settings_tab()  # General application settings
def notifications_tab()  # Notification preferences
def database_management_tab()  # Database maintenance tools
def advanced_settings_tab()  # Advanced settings
```

#### trading.py (60 lines)

**Imports:** `pandas, streamlit`

```python
def trading_page()  # Trading interface
```


### `dashboard/styles/`

#### theme.py (475 lines)


### `dashboard/utils/`

#### data_loader.py (131 lines)

**Imports:** `data_sources, database, datetime, numpy, pandas, pathlib, streamlit, sys`

```python
def get_database()  # Get cached database instance
def get_nse()  # Get cached NSE data source - NOW EXPORTED
def get_updater()  # Get cached updater instance
def load_stock_data(symbol:str)  # Load complete stock data with caching
def calculate_metrics(price_history:pd.DataFrame, snapshot:dict)  # Calculate key performance metrics
```

#### formatters.py (277 lines)

**Imports:** `datetime, numpy, pandas, typing`

```python
def safe_num(value:Any, default:float=0)  # Safely convert any value to float
def safe_format_currency(value:Any, decimals:int=2, default:str='N/A', symbol:str='₹')  # Format value as currency with symbol
def safe_format_percent(value:Any, decimals:int=2, default:str='N/A', include_sign:bool=False)  # Format value as percentage
def safe_format_number(value:Any, decimals:int=0, default:str='N/A', abbreviate:bool=False)  # Format value as number with thousand separators
def safe_get_dict_value(data:dict, key:str, default:str='N/A', format_func:Optional[callable]=None)  # Safely retrieve and optionally format dictionary value
def format_time_ago(dt:Union[datetime, str, None])  # Format datetime as human-readable "time ago"
def format_large_number(value:Any)  # Format large numbers with Indian numbering system
def parse_indian_number(value:str)  # Parse Indian formatted numbers
def format_market_cap(value:Any)  # Format market cap in standard financial notation
def color_code_change(value:float)  # Return color class based on value (for price changes)
```


### `data_sources/`

#### __init__.py (8 lines)

**Imports:** `base_source, nse_complete`

#### base_source.py (53 lines)

**Imports:** `abc, logging, pandas, typing`

```python
class DataSource(ABC)  # Base class for all data sources.
    __init__(self, name:str)
    get_company_info(self, symbol:str)  # Get basic company information.
    get_price_data(self, symbol:str)  # Get current price and market data.
    get_historical_prices(self, symbol:str, period:str='1y', interval:str='1d')  # Get historical price data.
    test_connection(self)  # Test if the data source is accessible.
    handle_error(self, error:Exception, context:str='')  # Standardized error handling.
```

#### nse_complete.py (171 lines)

**Imports:** `base_source, datetime, logging, pandas, pathlib, sys, typing`

```python
class NSEComplete(DataSource)
    __init__(self)
    get_historical_prices(self, symbol:str, period:str='1y', interval:str='1d')  # Fulfills abstract method by mapping to self.master.get_histo
    get_price_data(self, symbol:str)  # Fulfills abstract method by mapping to self.nse.price_info()
    search(self, symbol:str, exchange='NSE', match:bool=False)  # Performs a search using the master list.
    get_company_info(self, symbol:str)
    __getattr__(self, name)  # Delegate calls to the wrapped nse or master instances.
```

#### nse_complete_ORIGINAL.py (258 lines)

**Imports:** `base_source, datetime, logging, nse_master_data, nse_utils, pandas, pathlib, sys, typing`

```python
class NSEComplete(DataSource)  # Complete NSE data source using:
    __init__(self)
    get_company_info(self, symbol:str)  # Get company information.
    get_price_data(self, symbol:str)  # Get current price data.
    get_historical_prices(self, symbol:str, period:str='1y', interval:str='1d')  # Get historical OHLCV data.
    get_intraday_data(self, symbol:str, interval:str='5m')  # Get today's intraday data.
    get_futures_data(self, symbol:str, expiry:str=None, period:str='1m', interval:str='1d')  # Get futures historical data.
    get_options_data(self, symbol:str, strike:int, option_type:str, expiry:str=None, interval:str='5m')  # Get options historical data.
    get_option_chain(self, symbol:str, indices:bool=True)  # Get full option chain.
    get_market_depth(self, symbol:str)  # Get bid/ask depth.
    get_corporate_actions(self, from_date:str=None, to_date:str=None, filter:str=None)  # Get corporate actions.
    get_bulk_deals(self, from_date:str=None, to_date:str=None)  # Get bulk deals.
    get_insider_trading(self, from_date:str=None, to_date:str=None)  # Get insider trading data.
    get_complete_data(self, symbol:str)  # Get complete dataset for a symbol.
```

#### screener_enhanced.py (127 lines)

**Imports:** `base_source, bs4, io, logging, pandas, re, requests, typing`

```python
class ScreenerEnhanced(DataSource)  # Enhanced Screener.in scraper with complete data extraction.
    __init__(self)
    _parse_number(self, value:Any)  # Safely parse a string into a float, handling commas and symb
    _get_company_page(self, symbol:str)  # Fetch and parse company page using requests.
    get_complete_data(self, symbol:str)  # Get ALL available data from Screener.
    _extract_company_info(self, soup:BeautifulSoup, symbol:str)
    _extract_key_metrics(self, soup:BeautifulSoup)
    _extract_table(self, soup:BeautifulSoup, table_id:str, is_peers:bool=False)
    get_company_info(self, symbol:str)
    get_price_data(self, symbol:str)
    get_historical_prices(self, symbol:str, period:str='1y', interval:str='1d')
```

#### yahoo_finance.py (97 lines)

**Imports:** `base_source, datetime, logging, pandas, typing, yfinance`

```python
class YahooFinance(DataSource)  # Yahoo Finance API wrapper.
    __init__(self)
    _get_ticker(self, symbol:str)  # Get Yahoo Finance ticker object.
    get_company_info(self, symbol:str)  # Get company information.
    get_price_data(self, symbol:str)  # Get current price data.
    get_historical_prices(self, symbol:str, period:str='1y', interval:str='1d')  # Get historical price data.
```


### `database/`

#### __init__.py (9 lines)

**Imports:** `db_manager, updater`

#### db_manager.py (809 lines)

**Imports:** `datetime, json, logging, pandas, pathlib, schema, sqlite3, typing`

```python
class DatabaseManager  # Manage SQLite database operations with hybrid schema.
    __init__(self, db_path:str='stock_data.db')
    _initialize_db(self)  # Initialize database and create tables.
    _verify_schema(self)  # Verify all tables were created.
    execute(self, query:str, params:tuple=None)  # Execute a SQL query.
    executemany(self, query:str, params_list:List[tuple])  # Execute a SQL query with multiple parameter sets.
    commit(self)  # Commit changes.
    rollback(self)  # Rollback changes.
    begin_transaction(self)  # Begin a transaction.
    add_company(self, symbol:str, company_name:str=None, sector:str=None, industry:str=None, isin:str=None, listing_date:str=None)  # Add or update company in master table.
    get_company(self, symbol:str)  # Get company information.
    get_all_companies(self, sector:str=None)  # Get all companies, optionally filtered by sector.
    get_sectors(self)  # Get list of unique sectors.
    update_snapshot(self, symbol:str, data:Dict)  # Update latest snapshot for a company.
    get_snapshot(self, symbol:str)  # Get latest snapshot for a symbol.
    get_all_snapshots(self)  # Get all latest snapshots.
    save_price_history(self, symbol:str, df:pd.DataFrame)  # Save historical OHLCV data.
    get_price_history(self, symbol:str, days:int=365, start_date:str=None, end_date:str=None)  # Get historical prices.
    get_latest_price_date(self, symbol:str)  # Get the date of the latest price record.
    save_quarterly_results(self, symbol:str, df:pd.DataFrame)  # Save quarterly results.
    get_quarterly_results(self, symbol:str, limit:int=12)  # Get quarterly results.
    save_annual_results(self, symbol:str, df:pd.DataFrame)  # Save annual profit & loss results.
    get_annual_results(self, symbol:str, limit:int=10)  # Get annual results.
    save_shareholding(self, symbol:str, df:pd.DataFrame)  # Save shareholding pattern.
    get_shareholding(self, symbol:str, limit:int=8)  # Get shareholding pattern.
    save_peers(self, symbol:str, df:pd.DataFrame)  # Save peer comparison.
    get_peers(self, symbol:str)  # Get peer comparison.
    save_custom_metric(self, symbol:str, metric_name:str, metric_value:Any, metric_type:str='text', period:str=None, category:str='custom')  # Save a custom metric (flexible EAV pattern).
    get_custom_metrics(self, symbol:str, category:str=None, period:str=None)  # Get custom metrics.
    log_update(self, symbol:str, table_name:str, record_count:int=0, status:str='success', message:str=None, execution_time:float=None)  # Log a data update.
    get_last_update(self, symbol:str, table_name:str=None)  # Get last successful update time.
    get_update_summary(self)  # Get update summary for all stocks.
    needs_update(self, symbol:str, hours:int=24)  # Check if stock needs update.
    _parse_number(self, value)  # Parse number from string (handles ₹, %, commas).
    _parse_percentage(self, value)  # Parse percentage value.
    get_table_info(self, table_name:str)  # Get table schema information.
    get_row_count(self, table_name:str)  # Get row count for a table.
    get_database_stats(self)  # Get database statistics.
    vacuum(self)  # Optimize database (reclaim space).
    close(self)  # Close database connection.
```

#### schema.py (1101 lines)

#### updater.py (448 lines)

**Imports:** `core, datetime, db_manager, logging, re, time, typing`

```python
class DataUpdater  # Update database with fresh data from all sources.
    __init__(self, db_path:str='stock_data.db')
    update_stock(self, symbol:str, force:bool=False)  # Update all data for a symbol.
    _update_company_info(self, symbol:str, data:Dict)  # Update company master table.
    _update_snapshot(self, symbol:str, data:Dict)  # Update latest snapshot.
    _update_price_history(self, symbol:str, data:Dict)  # Update historical prices.
    _update_quarterly_results(self, symbol:str, data:Dict)  # Update quarterly results.
    _update_annual_results(self, symbol:str, data:Dict)  # Update annual results.
    _update_shareholding(self, symbol:str, data:Dict)  # Update shareholding pattern.
    _update_peers(self, symbol:str, data:Dict)  # Update peer comparison.
    _update_corporate_actions(self, symbol:str, data:Dict)  # Update corporate actions.
    update_multiple(self, symbols:List[str], force:bool=False, delay:float=2.0)  # Update multiple stocks with rate limiting.
    _print_batch_summary(self, results:Dict[str, Dict])  # Print summary of batch update.
    update_stale_stocks(self, hours:int=24, max_stocks:int=None)  # Update stocks that haven't been updated recently.
    update_sector(self, sector:str, force:bool=False)  # Update all stocks in a sector.
    _extract_number(self, value)  # Extract numeric value from string.
    get_update_status(self)  # Get current update status of database.
```


### `./`

#### debug_master.py (70 lines)

**Imports:** `pandas, pathlib, sys`


### `examples/`

#### example_basic_usage.py (121 lines)

**Imports:** `core, pandas, pathlib, sys`

```python
def example_single_stock()  # Fetch data for a single stock.
def example_quick_quotes()  # Get quick quotes for multiple stocks.
def example_batch_fetch()  # Batch fetch multiple stocks.
def example_cache_performance()  # Demonstrate caching performance.
```

#### example_technical_analysis.py (138 lines)

**Imports:** `core, data_sources, numpy, pandas, pathlib, sys`

```python
def calculate_moving_averages(df, periods=[20, 50, 200])  # Calculate simple moving averages.
def calculate_rsi(df, period=14)  # Calculate RSI indicator.
def example_moving_averages()  # Calculate and display moving averages.
def example_intraday_analysis()  # Analyze intraday data.
def example_rsi_analysis()  # Calculate RSI indicator.
```


### `external_libs/`

#### __init__.py (3 lines)

#### nse_master_data.py (181 lines)

**Imports:** `datetime, json, pandas, re, requests, time`

```python
class NSEMasterData
    __init__(self)
    get_nse_symbol_master(self, url)  # CORRECTED: Fetches and correctly parses the symbol master, u
    download_symbol_master(self)  # Download NSE and NFO master data and assigns them to interna
    search(self, symbol, exchange, match=False)  # Search for symbols, now using the correct 'TradingSymbol' co
    search_symbol(self, symbol, exchange)  # Search for a symbol and return the first match, using correc
    get_history(self, symbol='Nifty 50', exchange='NSE', start=None, end=None, interval='1d')  # Get historical data for a symbol. This is the complete, orig
```

#### nse_utils.py (1185 lines)

**Imports:** `datetime, io, pandas, requests, zipfile`

```python
class NseUtils
    __init__(self)
    pre_market_info(self, category='All')
    get_index_details(self, category, list_only=False)
    clearing_holidays(self, list_only=False)  # Returns the list of NSE clearing holidays
    trading_holidays(self, list_only=False)  # Returns the list of NSE trading holidays
    is_nse_trading_holiday(self, date_str=None)  # Return True if the date supplied in a NSE trading holiday, e
    is_nse_clearing_holiday(self, date_str=None)  # Return True if the date supplied in a NSE clearing holiday, 
    equity_info(self, symbol)  # Extracts the full details of a symbol as see on NSE website
    price_info(self, symbol)  # Gets all key price related information for a given stock
    futures_data(self, symbol, indices=False)  # Returns the list of futures instruments for a given stock an
    get_option_chain(self, symbol, indices=False)  # Returns the full option chain table as seen on NSE website f
    get_52week_high_low(self, stock=None)  # Get 52 Week High and Low data.  If stock is provided, the Hi
    fno_bhav_copy(self, trade_date:str='')  # Get the NSE FNO bhav copy data as per the traded date
    bhav_copy_with_delivery(self, trade_date:str)  # Get the NSE bhav copy with delivery data as per the traded d
    equity_bhav_copy(self, trade_date:str)  # Extract Equity Bhav Copy per the traded date provided
    bhav_copy_indices(self, trade_date:str)  # Get nse bhav copy as per the traded date provided
    fii_dii_activity(self)  # FII and DII trading activity of the day in data frame
    get_live_option_chain(self, symbol:str, expiry_date:str=None, oi_mode:str='full', indices=False)  # get live nse option chain.
    get_market_depth(self, symbol)  # Function to retrieve market depth for a given symbol
    get_index_historic_data(self, index:str, from_date:str=None, to_date:str=None)  # get historical index data set for the specific time period.
    get_index_data(self, index:str, from_date:str, to_date:str)
    get_equity_full_list(self, list_only=False)  # get list of all equity available to trade in NSE
    get_fno_full_list(self, list_only=False)  # get a dataframe of all listed derivative list with the recen
    get_gainers_losers(self)
    get_corporate_action(self, from_date_str:str=None, to_date_str:str=None, filter:str=None)
    get_corporate_announcement(self, from_date_str:str=None, to_date_str:str=None)
    get_index_pe_ratio(self)
    get_index_pb_ratio(self)
    get_index_div_yield(self)
    get_advance_decline(self)
    most_active_equity_stocks_by_volume(self)
    most_active_equity_stocks_by_value(self)
    most_active_index_calls(self)
    most_active_index_puts(self)
    most_active_stock_calls(self)
    most_active_stock_puts(self)
    most_active_contracts_by_oi(self)
    most_active_contracts_by_volume(self)
    most_active_futures_contracts_by_volume(self)
    most_active_options_contracts_by_volume(self)
    get_insider_trading(self, from_date:str=None, to_date:str=None)
    get_upcoming_results_calendar(self)
    get_etf_list(self)
    get_bulk_deals(self, from_date:str=None, to_date:str=None)
    get_block_deals(self, from_date:str=None, to_date:str=None)
    get_short_selling(self, from_date:str=None, to_date:str=None)
```


### `./`

#### final_cleanup.py (178 lines)

**Imports:** `argparse, os, pathlib, shutil`

```python
class ProjectCleaner
    __init__(self, project_root=None)
    log(self, message, emoji='ℹ️')
    create_scripts_dir(self)  # Create scripts directory if it doesn't exist
    delete_temp_files(self, dry_run=False)  # Delete temporary refactoring scripts
    move_utility_scripts(self, dry_run=False)  # Move utility scripts to scripts/ folder
    cleanup_failed_backups(self, dry_run=False)  # Remove failed refactoring backup folders
    cleanup_pycache(self, dry_run=False)  # Remove all __pycache__ directories
    create_readme_for_scripts(self, dry_run=False)  # Create README in scripts folder
```

#### fix_corporate_actions.py (77 lines)

**Imports:** `pandas, pathlib, sys`

```python
def fix_corporate_actions(csv_path:str)  # Fix corporate actions CSV:
def main()
```

#### fix_nse_merge.py (289 lines)

**Imports:** `ast, datetime, os, pathlib, re, sys`

```python
def extract_class_body(content:str, class_name:str)  # Extract everything inside a class definition
def normalize_indentation(code:str, target_indent:int=4)  # Normalize code indentation to target level
```

#### fix_streamlit_warnings.py (72 lines)

**Imports:** `pathlib, re`

```python
def fix_file(filepath:Path)  # Fix a single file
def main()
```

#### quick_validate.py (166 lines)

**Imports:** `pathlib, sys`

#### restaurant_shift_manager.py (183 lines)

**Imports:** `datetime, pandas, tkinter`

```python
class ShiftManagerApp
    __init__(self, root)
    setup_ui(self)
    add_staff(self)
    mark_time(self)
    calculate_hours(self, s)  # Compute total working hours = (Logout - Start) - (Break End 
    update_tree(self, index, s)
    delete_staff(self)
    export_to_excel(self)
```

#### restaurant_shift_manager_v5.py (769 lines)

**Imports:** `csv, datetime, io, pandas, tkinter`

```python
def generate_time_options(granularity_minutes=15)  # Generates time options in HH:MM format for comboboxes.
def parse_time_str(tstr)  # Safely parses HH:MM string to a datetime.time object.
def to_datetime_today(t)  # Converts datetime.time to a datetime object on the current d
def normalize_interval_minutes(v)  # Ensures interval is 15, 30, or 60 minutes.
class StaffRecord
    __init__(self, name, role, dept, start='', break_start='', break_end='', logout='')
    get_datetimes(self)  # Calculates adjusted datetimes for overnight shifts.
    working_hours(self)
    break_hours(self)
    total_hours(self)
    to_dict(self)
class ShiftManagerApp
    __init__(self, root)
    create_ui(self)
    build_staff_tab(self)
    filter_staff_tree(self)
    clear_filters(self)
    insert_staff_tree(self, rec)
    add_staff(self)
    clear_inputs(self)
    on_tree_select(self, ev)
    update_selected(self)
    delete_selected(self)
    import_csv(self)
    download_sample_csv(self)
    export_excel(self)
    export_csv(self)
    build_view_tab(self)
    refresh_view(self)
    build_stats_tab(self)
    refresh_stats_tab(self)
    generate_suggestions(self)
```

#### restaurant_shift_manager_v6_grok.py (548 lines)

**Imports:** `csv, datetime, io, os, pandas, tkinter`

```python
def parse_time_safe(tstr)
def fmt_time(dt)
class StaffRecord
    __init__(self, name, role, dept, start='', break_start='', break_end='', logout='')
    to_dict(self)
    working_hours(self)
    break_hours(self)
class ShiftManagerApp
    __init__(self, master)
    create_widgets(self)
    build_staff_tab(self)
    build_shift_view_tab(self)
    _on_canvas_configure(self, event)
    add_staff(self)
    _insert_staff_tree(self, rec)
    clear_inputs(self)
    on_staff_select(self, event)
    update_selected_staff(self)
    delete_selected_staff(self)
    import_csv(self)
    download_sample_csv(self)
    export_excel(self)
    export_csv(self)
    refresh_shift_view(self)
```

#### stock_screener.py (152 lines)

**Imports:** `core, pandas, re, time, typing`

```python
class FundamentalScreener  # Screen stocks based on fundamental criteria.
    __init__(self)
    screen_stocks(self, symbols:List[str], min_roe:float=None, max_pe:float=None, min_roce:float=None, min_div_yield:float=None)  # Screen stocks based on fundamental filters.
    _extract_number(self, value:str)  # Extract numeric value from string like '15.5%' or '₹1,234'.
def main()  # Example usage.
```

#### structure.py (382 lines)

**Imports:** `ast, datetime, os, pathlib, subprocess, sys`

```python
def find_git_root(start_path=None)  # Find the root of the git repository.
def find_project_root()  # Automatically detect project root directory.
def scan_python_files(base_dir)  # Recursively find Python files.
def compact_signature(func_node)  # Generate ultra-compact function signature.
def extract_compact_info(file_path, project_root)  # Extract minimal essential information.
def generate_tree_structure(files, project_root)  # Generate compact tree structure.
def generate_compact_output(project_root, files)  # Generate ultra-compact text output optimized for LLM.
def generate_markdown_output(project_root, files)  # Generate compact markdown output.
def generate_minimal_json(project_root, files)  # Generate minimal JSON (more compact than original).
def save_outputs(project_root, files)  # Save multiple output formats.
def main()  # Main function.
```

#### test_components.py (187 lines)

**Imports:** `argparse, pathlib, sys`

```python
def test_nse_detailed()  # Detailed NSE testing
def test_yahoo_detailed()  # Detailed Yahoo Finance testing
def test_database_detailed()  # Detailed database testing
def test_aggregator_detailed()  # Detailed aggregator testing
def main()
```

#### test_health_check.py (376 lines)

**Imports:** `pathlib, sys, traceback`

```python
def test_result(passed:bool, test_name:str, details:str='')  # Print colored test result
def test_imports()  # Test 1: Check if core modules can be imported
def test_data_sources()  # Test 2: Check if data sources are accessible
def test_database()  # Test 3: Database operations
def test_core_functionality()  # Test 4: Core functionality
def test_dashboard()  # Test 5: Dashboard components
def print_summary(all_results)  # Print overall summary
def main()  # Run all tests
```


### `tests/_helpers/`

#### fake_dataframes.py (14 lines)

**Imports:** `pandas`

```python
def sample_price_history(symbol='TCS', rows=5)
def sample_intraday(symbol='TCS', rows=10, interval='5m')
```

#### fake_streamlit.py (8 lines)

```python
class FakeStreamlit
    __getattr__(self, name)
```

#### mock_responses.py (30 lines)

**Imports:** `datetime, pandas`

```python
def mock_nse_price_info(symbol='TCS')
def mock_nse_option_chain(symbol='NIFTY', indices=True)
def mock_yf_history(days=30)
def mock_screener_company_page(symbol='TCS')
```

#### temp_dirs.py (10 lines)

**Imports:** `shutil, tempfile`

```python
class TempDir
    __init__(self)
    cleanup(self)
```


### `tests/`

#### conftest.py (38 lines)

**Imports:** `datetime, pandas, unittest`

```python
def mock_requests_get()
```

#### run_all_tests.py (24 lines)

**Imports:** `pathlib, sys, unittest`

```python
def main()
```


### `tests/test_core/`

#### test_cache_manager.py (29 lines)

**Imports:** `core, pathlib, shutil, unittest`

```python
class TestCacheManager(unittest.TestCase)
    setUp(self)
    tearDown(self)
    test_set_get_clear_stats(self)
    test_expiry(self)
```

#### test_data_merger.py (22 lines)

**Imports:** `core, unittest`

```python
class TestDataMerger(unittest.TestCase)
    test_merge_price_data_priority(self)
    test_validate_price_data(self)
class TestDataQualityChecker(unittest.TestCase)
    test_assess_quality(self)
```

#### test_hybrid_aggregator.py (24 lines)

**Imports:** `core, unittest`

```python
class TestHybridAggregator(unittest.TestCase)
    test_get_stock_data(self, mock_yf_hist, mock_screener, mock_nse_price)
    test_batch_fetch(self)
```

#### test_model_data_prep.py (22 lines)

**Imports:** `core, pandas, unittest`

```python
class FakeNSE
    get_historical_prices(self, symbol, period='1y', interval='1d')
class FakeDB
    get_quarterly_results(self, symbol, limit=12)
    get_annual_results(self, symbol, limit=10)
    get_shareholding(self, symbol, limit=8)
class TestModelDataPrep(unittest.TestCase)
    setUp(self)
    test_prepare_price_prediction_data(self)
```

#### test_mtf_manager.py (20 lines)

**Imports:** `core, pandas, unittest`

```python
class FakeDB
class FakeNSE
    get_intraday_data(self, symbol, interval='5m')
class TestMTFManager(unittest.TestCase)
    test_timeframe_conversions(self)
    test_get_mtf_data(self)
```

#### test_rate_limiter.py (11 lines)

**Imports:** `core, time, unittest`

```python
class TestRateLimiter(unittest.TestCase)
    test_wait_if_needed(self)
```


### `tests/`

#### test_core_modules.py (67 lines)

**Imports:** `core, pandas, tests, time, unittest`

```python
class TestCoreModules(unittest.TestCase)
    test_cache_manager_set_get(self)  # Unit test for CacheManager TTL and retrieval.
    test_rate_limiter_wait(self)  # Unit test for RateLimiter token bucket logic.
    test_data_merger_price_priority(self)  # Unit test for DataMerger conflict resolution.
    test_hybrid_aggregator_call_flow(self, mock_fetch, mock_quality)  # Integration test for HybridAggregator combining fetch and qu
```


### `tests/test_dashboard/`

#### test_app.py (11 lines)

**Imports:** `dashboard, unittest`

```python
class TestDashboardApp(unittest.TestCase)
    test_validate_nse_symbol(self, mock_get_nse)
```

#### test_components.py (9 lines)

**Imports:** `dashboard, pandas, unittest`

```python
class TestComponents(unittest.TestCase)
    test_render_quarterly_results(self)
```

#### test_pages.py (10 lines)

**Imports:** `dashboard, pandas, unittest`

```python
class TestPages(unittest.TestCase)
    test_render_price_trend_chart(self, _)
```

#### test_utils.py (12 lines)

**Imports:** `dashboard, datetime, unittest`

```python
class TestUtils(unittest.TestCase)
    test_currency(self)
    test_time_ago(self)
```


### `tests/`

#### test_data_sources.py (38 lines)

**Imports:** `data_sources, pandas, tests, unittest`

```python
class TestDataSources(unittest.TestCase)
    setUp(self)
    test_nse_complete_price_data(self, mock_get)  # Unit test for NSEComplete.get_price_data.
    test_nse_complete_historical_prices(self, mock_historic)  # Unit test for NSEComplete.get_historical_prices using intern
    test_screener_enhanced_fundamental(self, mock_get)  # Unit test for ScreenerEnhanced parsing logic.
```


### `tests/test_data_sources/`

#### test_base_source.py (17 lines)

**Imports:** `data_sources, unittest`

```python
class Dummy(DataSource)
    __init__(self)
    get_company_info(self, symbol)
    get_price_data(self, symbol)
    get_historical_prices(self, symbol, period='1y', interval='1d')
    test_connection(self)
class TestBaseSource(unittest.TestCase)
    test_error_handling(self)
```

#### test_nse_complete_integration.py (14 lines)

**Imports:** `data_sources, unittest`

```python
class TestNSECompleteIntegration(unittest.TestCase)
    test_get_complete_data(self, mock_bhav, mock_price)
```

#### test_nse_complete_unit.py (26 lines)

**Imports:** `data_sources, unittest`

```python
class TestNSECompleteUnit(unittest.TestCase)
    setUp(self)
    test_get_price_data(self, mock_price)
    test_get_option_chain(self, mock_chain)
    test_search_symbol(self, mock_search)
```

#### test_screener_enhanced.py (14 lines)

**Imports:** `data_sources, unittest`

```python
class TestScreenerEnhanced(unittest.TestCase)
    test_get_complete_data(self, mock_page)
```

#### test_yahoo_finance.py (22 lines)

**Imports:** `data_sources, unittest`

```python
class FakeTicker
    info(self)
    history(self, period='1y', interval='1d')
class TestYahooFinance(unittest.TestCase)
    test_get_company_info(self, _)
    test_get_historical_prices(self, _)
```


### `tests/test_database/`

#### test_db_manager.py (25 lines)

**Imports:** `database, os, pandas, tempfile, unittest`

```python
class TestDatabaseManager(unittest.TestCase)
    setUp(self)
    tearDown(self)
    test_add_and_get_company(self)
    test_price_history_roundtrip(self)
```

#### test_schema.py (8 lines)

**Imports:** `database, unittest`

```python
class TestSchema(unittest.TestCase)
    test_schema_has_core_tables(self)
```

#### test_updater.py (18 lines)

**Imports:** `database, unittest`

```python
class TestDataUpdater(unittest.TestCase)
    test_update_stock(self, mock_analysis)
```


### `tests/`

#### test_database_mtf.py (51 lines)

**Imports:** `core, database, pandas, tests, unittest`

```python
class TestDatabaseAndMTF(unittest.TestCase)
    setUp(self)
    test_db_manager_add_and_get_company(self)  # Integration test for basic DB CRUD operations.
    test_db_manager_save_and_load_price_data(self)  # Integration test for saving and loading historical data.
    test_timeframe_resample_ohlcv(self)  # Unit test for MTFDataManager._resample_ohlcv (aggregation lo
    test_mtf_manager_timeframe_conversions(self)  # Unit test for TimeFrame helper functions.
```


### `tests/test_examples/`

#### test_example_basic_usage.py (9 lines)

**Imports:** `examples, unittest`

```python
class TestExamplesBasic(unittest.TestCase)
    test_example_single_stock(self, _)
```

#### test_example_technical_analysis.py (9 lines)

**Imports:** `examples, pandas, unittest`

```python
class TestExamplesTA(unittest.TestCase)
    test_calculate_rsi(self)
```


### `tests/test_misc/`

#### test_structure_scripts.py (11 lines)

**Imports:** `structure, unittest`

```python
class TestStructureScripts(unittest.TestCase)
    test_find_project_root(self)
    test_scan_python_files(self)
```

#### test_unified_exporter.py (18 lines)

**Imports:** `pandas, unified_exporter, unittest`

```python
class TestUnifiedExporter(unittest.TestCase)
    test_export_to_excel(self, _)
```

#### test_validate_data.py (10 lines)

**Imports:** `pandas, unittest, validate_data`

```python
class TestValidateData(unittest.TestCase)
    test_validate_ohlcv(self)
```


### `tests/`

#### test_screener_enhanced.py (112 lines)

**Imports:** `data_sources, logging, pandas`


### `./`

#### unified_exporter.py (261 lines)

**Imports:** `core, datetime, json, pandas, pathlib, sys`

```python
class UnifiedExporter  # Export everything from NSE + Screener in one organized struc
    __init__(self, output_dir:str='stock_data')
    export_complete(self, symbol:str)  # Export everything for a symbol.
    _export_market_data(self, data, market_dir, summary)  # Export all NSE market data.
    _export_fundamentals(self, data, fundamental_dir, summary)  # Export all Screener fundamental data.
    _save_metadata(self, symbol_dir, summary)  # Save export metadata.
    _print_summary(self, symbol, summary)  # Print export summary.
    export_to_excel(self, symbol:str, filename:str=None)  # Export everything to a single Excel file with multiple sheet
def main()  # Example usage.
```

#### update_database.py (196 lines)

**Imports:** `argparse, database, logging, pathlib, sys`

```python
def main()  # Main CLI entry point.
def show_status(updater:DataUpdater)  # Show database status.
def list_sectors(updater:DataUpdater)  # List all sectors.
def print_result(result:dict)  # Print single stock update result.
```


### `utils/`

#### data_status.py (114 lines)

**Imports:** `logging, pandas, sqlite3, typing`

```python
def get_db_manager()  # Singleton pattern to get the DatabaseManager instance.
def fetch_table_statistics()  # Fetches the record count for all tables using the DatabaseMa
```


### `./`

#### validate_data.py (347 lines)

**Imports:** `datetime, numpy, pandas, pathlib`

```python
class DataValidator  # Validate all exported data for quality issues.
    __init__(self)
    validate_all_csvs(self, folder_path:str)  # Validate all CSV files in a folder.
    _validate_file(self, filename:str, df:pd.DataFrame)  # Validate a single CSV file.
    _validate_price_data(self, filename:str, df:pd.DataFrame)  # Validate price data.
    _validate_ohlcv_data(self, filename:str, df:pd.DataFrame)  # Validate OHLCV (candlestick) data.
    _validate_timestamps(self, filename:str, df:pd.DataFrame)  # Validate date/timestamp columns.
    _check_date_gaps(self, filename:str, dates:pd.DatetimeIndex)  # Check for unusual gaps in date sequence.
    _validate_date_columns(self, filename:str, df:pd.DataFrame)  # Validate files with date columns (corporate actions, bulk de
    _validate_company_info(self, filename:str, df:pd.DataFrame)  # Validate company information.
    _check_missing_values(self, filename:str, df:pd.DataFrame)  # Check for missing values.
    _print_summary(self)  # Print validation summary.
def main()  # Run validation on a folder.
```
