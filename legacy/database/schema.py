# database/schema.py

"""
Complete NSE ML Database Schema
- Optimized for ML feature engineering
- Covers all critical NSE data points
- Hybrid design: Denormalized (speed) + EAV (flexibility)
"""

CREATE_TABLES = """
-- ============================================================
-- MASTER TABLES
-- ============================================================

-- Companies master table (single source of truth)
CREATE TABLE IF NOT EXISTS companies (
    symbol TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    isin TEXT,
    listing_date DATE,
    market_cap_category TEXT,  -- 'Large Cap', 'Mid Cap', 'Small Cap'
    is_fno_enabled BOOLEAN DEFAULT 0,
    is_index_constituent BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Latest snapshot (current state - fast access)
CREATE TABLE IF NOT EXISTS latest_snapshot (
    symbol TEXT PRIMARY KEY,
    current_price REAL,
    prev_close REAL,
    open REAL,
    day_high REAL,
    day_low REAL,
    change REAL,
    change_percent REAL,
    volume INTEGER,
    market_cap TEXT,
    pe_ratio REAL,
    pb_ratio REAL,
    roe REAL,
    roce REAL,
    dividend_yield REAL,
    eps REAL,
    book_value REAL,
    face_value REAL,
    high_52w REAL,
    low_52w REAL,
    upper_circuit REAL,
    lower_circuit REAL,
    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- ============================================================
-- PRICE DATA (Core ML Features)
-- ============================================================

-- Historical OHLCV data (Daily)
CREATE TABLE IF NOT EXISTS price_history (
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
    UNIQUE(symbol, date),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Intraday prices (for intraday ML models)
CREATE TABLE IF NOT EXISTS intraday_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,  -- '1m', '5m', '15m', '30m', '1h'
    timestamp TIMESTAMP NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timeframe, timestamp),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- ============================================================
-- CORPORATE ACTIONS (Critical for price adjustment)
-- ============================================================

-- Corporate actions (dividends, splits, bonuses, etc.)
CREATE TABLE IF NOT EXISTS corporate_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    ex_date DATE,
    record_date DATE,
    purpose TEXT,
    details TEXT,
    action_type TEXT,  -- 'dividend', 'split', 'bonus', 'rights', 'buyback'
    dividend_amount REAL,
    split_ratio TEXT,
    bonus_ratio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Corporate announcements (for NLP/event analysis)
CREATE TABLE IF NOT EXISTS corporate_announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    announcement_date DATE,
    subject TEXT,
    description TEXT,
    category TEXT,  -- 'results', 'merger', 'acquisition', 'general'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Upcoming results calendar
CREATE TABLE IF NOT EXISTS results_calendar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    result_date DATE,
    result_type TEXT,  -- 'quarterly', 'annual'
    financial_year TEXT,
    quarter TEXT,
    is_announced BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- ============================================================
-- INSTITUTIONAL ACTIVITY (High predictive value)
-- ============================================================

-- FII/DII daily activity (Market-level)
CREATE TABLE IF NOT EXISTS fii_dii_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    fii_buy_value REAL,
    fii_sell_value REAL,
    fii_net_value REAL,
    dii_buy_value REAL,
    dii_sell_value REAL,
    dii_net_value REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bulk deals (Large transactions)
CREATE TABLE IF NOT EXISTS bulk_deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    deal_date DATE,
    client_name TEXT,
    deal_type TEXT,  -- 'buy' or 'sell'
    quantity INTEGER,
    price REAL,
    value REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Block deals (Institutional trades)
CREATE TABLE IF NOT EXISTS block_deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    deal_date DATE,
    client_name TEXT,
    deal_type TEXT,  -- 'buy' or 'sell'
    quantity INTEGER,
    price REAL,
    value REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Insider trading
CREATE TABLE IF NOT EXISTS insider_trading (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    person_name TEXT,
    person_category TEXT,  -- 'Promoter', 'Director', 'Employee'
    securities_type TEXT,
    transaction_type TEXT,  -- 'buy' or 'sell'
    number_of_securities INTEGER,
    value REAL,
    acquisition_date DATE,
    intimation_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Short selling data
CREATE TABLE IF NOT EXISTS short_selling (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE,
    short_qty INTEGER,
    short_value REAL,
    total_qty INTEGER,
    short_percent REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- ============================================================
-- DERIVATIVES DATA (Options & Futures)
-- ============================================================

-- Futures data
CREATE TABLE IF NOT EXISTS futures_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    expiry_date DATE,
    timestamp TIMESTAMP,
    underlying_value REAL,
    futures_price REAL,
    open_interest INTEGER,
    oi_change INTEGER,
    volume INTEGER,
    basis REAL,  -- futures_price - underlying_value
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, expiry_date, timestamp),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Option chain data (snapshot)
CREATE TABLE IF NOT EXISTS option_chain (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    expiry_date DATE,
    strike_price REAL,
    option_type TEXT,  -- 'CE' or 'PE'
    timestamp TIMESTAMP,
    underlying_value REAL,
    last_price REAL,
    open_interest INTEGER,
    oi_change INTEGER,
    volume INTEGER,
    iv REAL,  -- Implied Volatility
    delta REAL,
    gamma REAL,
    theta REAL,
    vega REAL,
    bid_price REAL,
    ask_price REAL,
    bid_qty INTEGER,
    ask_qty INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, expiry_date, strike_price, option_type, timestamp),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Option chain aggregates (for PCR analysis)
CREATE TABLE IF NOT EXISTS option_chain_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    expiry_date DATE,
    date DATE,
    underlying_value REAL,
    total_call_oi INTEGER,
    total_put_oi INTEGER,
    pcr_oi REAL,  -- Put/Call Ratio (OI)
    total_call_volume INTEGER,
    total_put_volume INTEGER,
    pcr_volume REAL,  -- Put/Call Ratio (Volume)
    max_pain REAL,
    iv_percentile REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, expiry_date, date),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- ============================================================
-- INDEX DATA
-- ============================================================

-- Index master
CREATE TABLE IF NOT EXISTS indices (
    index_name TEXT PRIMARY KEY,
    index_symbol TEXT UNIQUE,
    description TEXT,
    constituents_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index historical data
CREATE TABLE IF NOT EXISTS index_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_symbol TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    pe_ratio REAL,
    pb_ratio REAL,
    div_yield REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(index_symbol, date),
    FOREIGN KEY (index_symbol) REFERENCES indices(index_symbol) ON DELETE CASCADE
);

-- Index constituents
CREATE TABLE IF NOT EXISTS index_constituents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_symbol TEXT NOT NULL,
    symbol TEXT NOT NULL,
    company_name TEXT,
    weightage REAL,
    effective_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(index_symbol, symbol, effective_date),
    FOREIGN KEY (index_symbol) REFERENCES indices(index_symbol) ON DELETE CASCADE,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- ============================================================
-- MARKET BREADTH & SENTIMENT
-- ============================================================

-- Daily market breadth
CREATE TABLE IF NOT EXISTS market_breadth (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    advances INTEGER,
    declines INTEGER,
    unchanged INTEGER,
    advance_decline_ratio REAL,
    new_highs INTEGER,
    new_lows INTEGER,
    stocks_above_200dma INTEGER,
    stocks_below_200dma INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Gainers and losers
CREATE TABLE IF NOT EXISTS gainers_losers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    symbol TEXT NOT NULL,
    category TEXT,  -- 'top_gainer', 'top_loser', 'most_active_volume', 'most_active_value'
    rank INTEGER,
    current_price REAL,
    change_percent REAL,
    volume INTEGER,
    value REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, symbol, category),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Pre-market data
CREATE TABLE IF NOT EXISTS pre_market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    symbol TEXT NOT NULL,
    prev_close REAL,
    pre_market_price REAL,
    change_percent REAL,
    category TEXT,  -- 'NIFTY 50', 'Nifty Bank', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, symbol),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- ============================================================
-- MARKET MICROSTRUCTURE (for HFT/advanced models)
-- ============================================================

-- Market depth snapshots
CREATE TABLE IF NOT EXISTS market_depth (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    bid_price_1 REAL, bid_qty_1 INTEGER, bid_orders_1 INTEGER,
    bid_price_2 REAL, bid_qty_2 INTEGER, bid_orders_2 INTEGER,
    bid_price_3 REAL, bid_qty_3 INTEGER, bid_orders_3 INTEGER,
    bid_price_4 REAL, bid_qty_4 INTEGER, bid_orders_4 INTEGER,
    bid_price_5 REAL, bid_qty_5 INTEGER, bid_orders_5 INTEGER,
    ask_price_1 REAL, ask_qty_1 INTEGER, ask_orders_1 INTEGER,
    ask_price_2 REAL, ask_qty_2 INTEGER, ask_orders_2 INTEGER,
    ask_price_3 REAL, ask_qty_3 INTEGER, ask_orders_3 INTEGER,
    ask_price_4 REAL, ask_qty_4 INTEGER, ask_orders_4 INTEGER,
    ask_price_5 REAL, ask_qty_5 INTEGER, ask_orders_5 INTEGER,
    total_bid_qty INTEGER,
    total_ask_qty INTEGER,
    spread REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- ============================================================
-- FUNDAMENTAL DATA
-- ============================================================

-- Quarterly results
CREATE TABLE IF NOT EXISTS quarterly_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    quarter TEXT NOT NULL,  -- 'Q1-2024', 'Q2-2024'
    financial_year TEXT,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percent REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percent REAL,
    net_profit REAL,
    eps REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, quarter),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Annual results
CREATE TABLE IF NOT EXISTS annual_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    year TEXT NOT NULL,  -- 'FY-2024'
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percent REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percent REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, year),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Balance sheet
CREATE TABLE IF NOT EXISTS balance_sheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    year TEXT NOT NULL,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    current_assets REAL,
    investments REAL,
    other_assets REAL,
    total_assets REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, year),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Cash flow statement
CREATE TABLE IF NOT EXISTS cash_flow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    year TEXT NOT NULL,
    operating_cash_flow REAL,
    investing_cash_flow REAL,
    financing_cash_flow REAL,
    net_cash_flow REAL,
    free_cash_flow REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, year),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Financial ratios
CREATE TABLE IF NOT EXISTS financial_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    year TEXT NOT NULL,
    debtor_days REAL,
    inventory_days REAL,
    days_payable REAL,
    cash_conversion_cycle REAL,
    working_capital_days REAL,
    roce REAL,
    roe REAL,
    debt_to_equity REAL,
    current_ratio REAL,
    quick_ratio REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, year),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Shareholding pattern
CREATE TABLE IF NOT EXISTS shareholding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    quarter TEXT NOT NULL,
    promoters REAL,
    fii REAL,
    dii REAL,
    public REAL,
    government REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, quarter),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- Peer comparison (FIXED - Added missing columns)
CREATE TABLE IF NOT EXISTS peers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    peer_symbol TEXT NOT NULL,
    peer_name TEXT,
    cmp REAL,
    pe REAL,
    market_cap REAL,
    div_yield REAL,
    np_qtr REAL,              -- Net Profit Quarterly (Rs. Cr.) - ADDED
    qtr_profit_var REAL,      -- Quarterly Profit Variance % - ADDED
    sales_qtr REAL,           -- Sales Quarterly (Rs. Cr.) - ADDED
    qtr_sales_var REAL,       -- Quarterly Sales Variance % - ADDED
    roce REAL,
    roe REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, peer_symbol),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- ============================================================
-- TECHNICAL INDICATORS (Pre-calculated for speed)
-- ============================================================

-- Technical indicators (optional - can be calculated on-the-fly)
CREATE TABLE IF NOT EXISTS technical_indicators (
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
    UNIQUE(symbol, date),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- ============================================================
-- HOLIDAYS & CALENDAR
-- ============================================================

-- Trading holidays
CREATE TABLE IF NOT EXISTS trading_holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    holiday_name TEXT,
    holiday_type TEXT,  -- 'trading', 'clearing', 'both'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- FLEXIBLE STORAGE (EAV Pattern)
-- ============================================================

-- Custom metrics (for experimental/future features)
CREATE TABLE IF NOT EXISTS custom_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value TEXT,
    metric_type TEXT,  -- 'numeric', 'text', 'date', 'percentage', 'json'
    period TEXT,  -- 'Q1-2024', 'FY-2024', '2024-01-15'
    category TEXT,  -- 'fundamental', 'technical', 'sentiment', 'ml_feature'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- ML features store (for pre-computed features)
CREATE TABLE IF NOT EXISTS ml_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    feature_set TEXT,  -- 'price_momentum', 'volatility', 'volume_profile'
    features_json TEXT,  -- JSON string of feature dict
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date, feature_set),
    FOREIGN KEY (symbol) REFERENCES companies(symbol) ON DELETE CASCADE
);

-- ============================================================
-- SYSTEM TABLES
-- ============================================================

-- Data update log
CREATE TABLE IF NOT EXISTS update_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    table_name TEXT NOT NULL,
    record_count INTEGER,
    status TEXT,  -- 'success', 'error', 'partial'
    message TEXT,
    execution_time REAL,  -- seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data sources metadata
CREATE TABLE IF NOT EXISTS data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT UNIQUE NOT NULL,  -- 'nse', 'screener', 'yahoo'
    is_active BOOLEAN DEFAULT 1,
    last_success TIMESTAMP,
    last_error TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    config_json TEXT,  -- JSON string for source-specific config
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

-- Price history indexes
CREATE INDEX IF NOT EXISTS idx_price_history_symbol ON price_history(symbol);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(date DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_symbol_date ON price_history(symbol, date DESC);

-- Intraday prices indexes
CREATE INDEX IF NOT EXISTS idx_intraday_symbol_tf ON intraday_prices(symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_intraday_timestamp ON intraday_prices(timestamp);
CREATE INDEX IF NOT EXISTS idx_intraday_lookup ON intraday_prices(symbol, timeframe, timestamp);

-- Corporate actions indexes
CREATE INDEX IF NOT EXISTS idx_corporate_actions_symbol ON corporate_actions(symbol);
CREATE INDEX IF NOT EXISTS idx_corporate_actions_date ON corporate_actions(ex_date DESC);
CREATE INDEX IF NOT EXISTS idx_corporate_actions_type ON corporate_actions(action_type);

-- FII/DII indexes
CREATE INDEX IF NOT EXISTS idx_fii_dii_date ON fii_dii_activity(date DESC);

-- Bulk/Block deals indexes
CREATE INDEX IF NOT EXISTS idx_bulk_deals_symbol ON bulk_deals(symbol);
CREATE INDEX IF NOT EXISTS idx_bulk_deals_date ON bulk_deals(deal_date DESC);
CREATE INDEX IF NOT EXISTS idx_block_deals_symbol ON block_deals(symbol);
CREATE INDEX IF NOT EXISTS idx_block_deals_date ON block_deals(deal_date DESC);

-- Insider trading indexes
CREATE INDEX IF NOT EXISTS idx_insider_symbol ON insider_trading(symbol);
CREATE INDEX IF NOT EXISTS idx_insider_date ON insider_trading(acquisition_date DESC);

-- Short selling indexes
CREATE INDEX IF NOT EXISTS idx_short_selling_symbol ON short_selling(symbol);
CREATE INDEX IF NOT EXISTS idx_short_selling_date ON short_selling(date DESC);

-- Futures indexes
CREATE INDEX IF NOT EXISTS idx_futures_symbol ON futures_data(symbol);
CREATE INDEX IF NOT EXISTS idx_futures_expiry ON futures_data(expiry_date);
CREATE INDEX IF NOT EXISTS idx_futures_timestamp ON futures_data(timestamp DESC);

-- Option chain indexes
CREATE INDEX IF NOT EXISTS idx_option_chain_symbol ON option_chain(symbol);
CREATE INDEX IF NOT EXISTS idx_option_chain_expiry ON option_chain(expiry_date);
CREATE INDEX IF NOT EXISTS idx_option_chain_strike ON option_chain(strike_price);
CREATE INDEX IF NOT EXISTS idx_option_chain_lookup ON option_chain(symbol, expiry_date, strike_price, option_type);

-- Index history indexes
CREATE INDEX IF NOT EXISTS idx_index_history_symbol ON index_history(index_symbol);
CREATE INDEX IF NOT EXISTS idx_index_history_date ON index_history(date DESC);

-- Market breadth indexes
CREATE INDEX IF NOT EXISTS idx_market_breadth_date ON market_breadth(date DESC);

-- Gainers/Losers indexes
CREATE INDEX IF NOT EXISTS idx_gainers_losers_date ON gainers_losers(date DESC);
CREATE INDEX IF NOT EXISTS idx_gainers_losers_category ON gainers_losers(category);

-- Technical indicators indexes
CREATE INDEX IF NOT EXISTS idx_technical_symbol ON technical_indicators(symbol);
CREATE INDEX IF NOT EXISTS idx_technical_date ON technical_indicators(date DESC);

-- ML features indexes
CREATE INDEX IF NOT EXISTS idx_ml_features_symbol ON ml_features(symbol);
CREATE INDEX IF NOT EXISTS idx_ml_features_date ON ml_features(date DESC);
CREATE INDEX IF NOT EXISTS idx_ml_features_set ON ml_features(feature_set);

-- Quarterly results indexes
CREATE INDEX IF NOT EXISTS idx_quarterly_symbol ON quarterly_results(symbol);
CREATE INDEX IF NOT EXISTS idx_quarterly_quarter ON quarterly_results(quarter DESC);

-- Annual results indexes
CREATE INDEX IF NOT EXISTS idx_annual_symbol ON annual_results(symbol);
CREATE INDEX IF NOT EXISTS idx_annual_year ON annual_results(year DESC);

-- Shareholding indexes
CREATE INDEX IF NOT EXISTS idx_shareholding_symbol ON shareholding(symbol);
CREATE INDEX IF NOT EXISTS idx_shareholding_quarter ON shareholding(quarter DESC);

-- Custom metrics indexes
CREATE INDEX IF NOT EXISTS idx_custom_metrics_symbol ON custom_metrics(symbol);
CREATE INDEX IF NOT EXISTS idx_custom_metrics_name ON custom_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_custom_metrics_category ON custom_metrics(category);

-- Update log indexes
CREATE INDEX IF NOT EXISTS idx_update_log_symbol ON update_log(symbol);
CREATE INDEX IF NOT EXISTS idx_update_log_created ON update_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_update_log_table ON update_log(table_name);

-- ============================================================
-- TRIGGERS (Auto-update timestamps)
-- ============================================================

CREATE TRIGGER IF NOT EXISTS update_companies_timestamp 
AFTER UPDATE ON companies
BEGIN
    UPDATE companies SET updated_at = CURRENT_TIMESTAMP WHERE symbol = NEW.symbol;
END;

CREATE TRIGGER IF NOT EXISTS update_snapshot_timestamp 
AFTER UPDATE ON latest_snapshot
BEGIN
    UPDATE latest_snapshot SET updated_at = CURRENT_TIMESTAMP WHERE symbol = NEW.symbol;
END;

CREATE TRIGGER IF NOT EXISTS update_quarterly_timestamp 
AFTER UPDATE ON quarterly_results
BEGIN
    UPDATE quarterly_results SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_annual_timestamp 
AFTER UPDATE ON annual_results
BEGIN
    UPDATE annual_results SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_index_constituents_timestamp 
AFTER UPDATE ON index_constituents
BEGIN
    UPDATE index_constituents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_custom_metrics_timestamp 
AFTER UPDATE ON custom_metrics
BEGIN
    UPDATE custom_metrics SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================
-- VIEWS (Pre-joined queries for common use cases)
-- ============================================================

-- Stock overview with latest data
CREATE VIEW IF NOT EXISTS v_stock_overview AS
SELECT 
    c.symbol,
    c.company_name,
    c.sector,
    c.industry,
    c.is_fno_enabled,
    ls.current_price,
    ls.change_percent,
    ls.volume,
    ls.market_cap,
    ls.pe_ratio,
    ls.pb_ratio,
    ls.roe,
    ls.roce,
    ls.dividend_yield,
    ls.high_52w,
    ls.low_52w,
    ls.updated_at as last_updated
FROM companies c
LEFT JOIN latest_snapshot ls ON c.symbol = ls.symbol;

-- Recent quarterly performance
CREATE VIEW IF NOT EXISTS v_recent_quarterly AS
SELECT 
    qr.symbol,
    c.company_name,
    qr.quarter,
    qr.sales,
    qr.net_profit,
    qr.opm_percent,
    qr.eps,
    qr.updated_at
FROM quarterly_results qr
JOIN companies c ON qr.symbol = c.symbol
ORDER BY qr.quarter DESC;

-- FII/DII activity summary
CREATE VIEW IF NOT EXISTS v_fii_dii_summary AS
SELECT 
    date,
    fii_net_value,
    dii_net_value,
    (fii_net_value + dii_net_value) as total_institutional_flow,
    CASE 
        WHEN fii_net_value > 0 AND dii_net_value > 0 THEN 'Bullish'
        WHEN fii_net_value < 0 AND dii_net_value < 0 THEN 'Bearish'
        ELSE 'Mixed'
    END as sentiment
FROM fii_dii_activity
ORDER BY date DESC;

-- Option chain PCR analysis
CREATE VIEW IF NOT EXISTS v_pcr_analysis AS
SELECT 
    symbol,
    expiry_date,
    date,
    pcr_oi,
    pcr_volume,
    max_pain,
    CASE 
        WHEN pcr_oi > 1.5 THEN 'Bullish'
        WHEN pcr_oi < 0.7 THEN 'Bearish'
        ELSE 'Neutral'
    END as sentiment_oi
FROM option_chain_summary
ORDER BY date DESC, symbol;

-- Insider trading summary
CREATE VIEW IF NOT EXISTS v_insider_summary AS
SELECT 
    symbol,
    transaction_type,
    COUNT(*) as transaction_count,
    SUM(number_of_securities) as total_securities,
    SUM(value) as total_value,
    MAX(acquisition_date) as latest_transaction
FROM insider_trading
WHERE acquisition_date >= date('now', '-90 days')
GROUP BY symbol, transaction_type
ORDER BY total_value DESC;

-- Market breadth trend
CREATE VIEW IF NOT EXISTS v_market_breadth_trend AS
SELECT 
    date,
    advances,
    declines,
    advance_decline_ratio,
    new_highs,
    new_lows,
    (new_highs - new_lows) as high_low_diff,
    CASE 
        WHEN advance_decline_ratio > 2 THEN 'Strong Bullish'
        WHEN advance_decline_ratio > 1 THEN 'Bullish'
        WHEN advance_decline_ratio < 0.5 THEN 'Strong Bearish'
        WHEN advance_decline_ratio < 1 THEN 'Bearish'
        ELSE 'Neutral'
    END as market_sentiment
FROM market_breadth
ORDER BY date DESC;

-- Update status summary
CREATE VIEW IF NOT EXISTS v_update_summary AS
SELECT 
    table_name,
    COUNT(*) as update_count,
    MAX(created_at) as last_update,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
    AVG(execution_time) as avg_execution_time
FROM update_log
GROUP BY table_name
ORDER BY last_update DESC;

-- Stock with strongest institutional buying
CREATE VIEW IF NOT EXISTS v_institutional_buying AS
SELECT 
    bd.symbol,
    c.company_name,
    COUNT(*) as deal_count,
    SUM(bd.value) as total_buy_value,
    AVG(bd.price) as avg_price
FROM bulk_deals bd
JOIN companies c ON bd.symbol = c.symbol
WHERE bd.deal_type = 'buy'
  AND bd.deal_date >= date('now', '-30 days')
GROUP BY bd.symbol, c.company_name
ORDER BY total_buy_value DESC
LIMIT 50;

-- ============================================================
-- INITIAL DATA
-- ============================================================

-- Insert data sources
INSERT OR IGNORE INTO data_sources (source_name, is_active) VALUES
    ('nse', 1),
    ('nse_utils', 1),
    ('nse_master', 1),
    ('screener', 1),
    ('yahoo', 1);

-- Insert major indices
INSERT OR IGNORE INTO indices (index_name, index_symbol, constituents_count) VALUES
    ('NIFTY 50', 'NIFTY', 50),
    ('NIFTY BANK', 'BANKNIFTY', 12),
    ('NIFTY IT', 'NIFTYIT', 10),
    ('NIFTY AUTO', 'NIFTYAUTO', 15),
    ('NIFTY PHARMA', 'NIFTYPHARMA', 10),
    ('NIFTY FMCG', 'NIFTYFMCG', 15),
    ('NIFTY METAL', 'NIFTYMETAL', 15),
    ('NIFTY REALTY', 'NIFTYREALTY', 10),
    ('NIFTY MIDCAP 50', 'NIFTYMIDCAP50', 50),
    ('NIFTY SMALLCAP 50', 'NIFTYSMALLCAP50', 50);
"""

# ============================================================
# UTILITY QUERIES
# ============================================================

DROP_ALL_TABLES = """
-- Drop views first
DROP VIEW IF EXISTS v_stock_overview;
DROP VIEW IF EXISTS v_recent_quarterly;
DROP VIEW IF EXISTS v_fii_dii_summary;
DROP VIEW IF EXISTS v_pcr_analysis;
DROP VIEW IF EXISTS v_insider_summary;
DROP VIEW IF EXISTS v_market_breadth_trend;
DROP VIEW IF EXISTS v_update_summary;
DROP VIEW IF EXISTS v_institutional_buying;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS ml_features;
DROP TABLE IF EXISTS custom_metrics;
DROP TABLE IF EXISTS trading_holidays;
DROP TABLE IF EXISTS technical_indicators;
DROP TABLE IF EXISTS peers;
DROP TABLE IF EXISTS shareholding;
DROP TABLE IF EXISTS financial_ratios;
DROP TABLE IF EXISTS cash_flow;
DROP TABLE IF EXISTS balance_sheet;
DROP TABLE IF EXISTS annual_results;
DROP TABLE IF EXISTS quarterly_results;
DROP TABLE IF EXISTS market_depth;
DROP TABLE IF EXISTS pre_market_data;
DROP TABLE IF EXISTS gainers_losers;
DROP TABLE IF EXISTS market_breadth;
DROP TABLE IF EXISTS index_constituents;
DROP TABLE IF EXISTS index_history;
DROP TABLE IF EXISTS indices;
DROP TABLE IF EXISTS option_chain_summary;
DROP TABLE IF EXISTS option_chain;
DROP TABLE IF EXISTS futures_data;
DROP TABLE IF EXISTS short_selling;
DROP TABLE IF EXISTS insider_trading;
DROP TABLE IF EXISTS block_deals;
DROP TABLE IF EXISTS bulk_deals;
DROP TABLE IF EXISTS fii_dii_activity;
DROP TABLE IF EXISTS results_calendar;
DROP TABLE IF EXISTS corporate_announcements;
DROP TABLE IF EXISTS corporate_actions;
DROP TABLE IF EXISTS intraday_prices;
DROP TABLE IF EXISTS price_history;
DROP TABLE IF EXISTS latest_snapshot;
DROP TABLE IF EXISTS update_log;
DROP TABLE IF EXISTS data_sources;
DROP TABLE IF EXISTS companies;
"""

# ============================================================
# TABLE LISTS
# ============================================================

ALL_TABLES = [
    # Master
    'companies',
    'latest_snapshot',
    
    # Price Data
    'price_history',
    'intraday_prices',
    
    # Corporate
    'corporate_actions',
    'corporate_announcements',
    'results_calendar',
    
    # Institutional
    'fii_dii_activity',
    'bulk_deals',
    'block_deals',
    'insider_trading',
    'short_selling',
    
    # Derivatives
    'futures_data',
    'option_chain',
    'option_chain_summary',
    
    # Index
    'indices',
    'index_history',
    'index_constituents',
    
    # Market
    'market_breadth',
    'gainers_losers',
    'pre_market_data',
    'market_depth',
    
    # Fundamentals
    'quarterly_results',
    'annual_results',
    'balance_sheet',
    'cash_flow',
    'financial_ratios',
    'shareholding',
    'peers',
    
    # Technical
    'technical_indicators',
    
    # Calendar
    'trading_holidays',
    
    # Flexible
    'custom_metrics',
    'ml_features',
    
    # System
    'update_log',
    'data_sources'
]

CORE_TABLES = [
    'companies',
    'price_history',
    'corporate_actions',
    'fii_dii_activity',
    'option_chain'
]

ML_CRITICAL_TABLES = [
    'price_history',
    'intraday_prices',
    'corporate_actions',
    'fii_dii_activity',
    'bulk_deals',
    'insider_trading',
    'option_chain',
    'futures_data',
    'index_history',
    'market_breadth',
    'technical_indicators',
    'ml_features'
]

# ============================================================
# TABLE CATEGORIES (for organized access)
# ============================================================

TABLE_CATEGORIES = {
    'price_data': ['price_history', 'intraday_prices', 'latest_snapshot'],
    'fundamentals': ['quarterly_results', 'annual_results', 'balance_sheet', 'cash_flow', 'financial_ratios', 'shareholding'],
    'derivatives': ['futures_data', 'option_chain', 'option_chain_summary'],
    'institutional': ['fii_dii_activity', 'bulk_deals', 'block_deals', 'insider_trading', 'short_selling'],
    'market_data': ['market_breadth', 'gainers_losers', 'pre_market_data', 'market_depth'],
    'index_data': ['indices', 'index_history', 'index_constituents'],
    'corporate': ['corporate_actions', 'corporate_announcements', 'results_calendar'],
    'technical': ['technical_indicators'],
    'ml': ['ml_features', 'custom_metrics'],
    'system': ['update_log', 'data_sources', 'trading_holidays']
}