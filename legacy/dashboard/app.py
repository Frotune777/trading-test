"""
Fortune Trading Dashboard - Professional Light Theme
With NSE Symbol Validation & SQL Query Interface
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager
from database.updater import DataUpdater
from data_sources.nse_complete import NSEComplete
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import io
import sqlite3

# Page config
st.set_page_config(
    page_title="Fortune Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Light Theme CSS
st.markdown("""
<style>
    /* Color Palette - Professional Light Theme */
    :root {
        --primary-blue: #2563EB;
        --primary-teal: #059669;
        --accent-orange: #EA580C;
        --accent-purple: #7C3AED;
        --success-green: #059669;
        --danger-red: #DC2626;
        --warning-yellow: #D97706;
        
        --bg-primary: #FFFFFF;
        --bg-secondary: #F9FAFB;
        --bg-tertiary: #F3F4F6;
        --border-color: #E5E7EB;
        --border-hover: #D1D5DB;
        
        --text-primary: #111827;
        --text-secondary: #4B5563;
        --text-muted: #6B7280;
        
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Global */
    .stApp {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }
    
    /* All text elements */
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label, 
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: var(--text-primary) !important;
    }
    
    /* Headers */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        color: var(--primary-blue) !important;
        text-align: center;
        margin: 1rem 0;
        padding: 1.5rem;
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.05), rgba(5, 150, 105, 0.05));
        border-radius: 12px;
        border: 2px solid var(--border-color);
        box-shadow: var(--shadow-sm);
    }
    
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--primary-teal) !important;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--border-color);
    }
    
    /* Cards */
    .metric-card {
        background: var(--bg-secondary);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        box-shadow: var(--shadow-sm);
    }
    
    .metric-card:hover {
        border-color: var(--primary-blue);
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-blue), var(--primary-teal)) !important;
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-sm);
    }
    
    .stButton>button:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-1px);
    }
    
    /* Input fields */
    .stTextInput>div>div>input, .stTextInput input, .stTextArea textarea {
        background: var(--bg-primary) !important;
        border: 2px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 8px;
        box-shadow: var(--shadow-sm);
    }
    
    .stTextInput>div>div>input:focus, .stTextArea textarea:focus {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }
    
    /* Select boxes */
    .stSelectbox>div>div>div, .stSelectbox select, .stSelectbox input {
        background: var(--bg-primary) !important;
        border: 2px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 8px;
    }
    
    /* Radio buttons */
    .stRadio > div {
        background: var(--bg-secondary);
        padding: 0.5rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }
    
    .stRadio label {
        color: var(--text-primary) !important;
    }
    
    /* Checkbox */
    .stCheckbox label {
        color: var(--text-primary) !important;
    }
    
    /* Download section */
    .download-section {
        background: var(--bg-secondary);
        padding: 2rem;
        border-radius: 12px;
        border: 2px solid var(--border-color);
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
    }
    
    .download-section:hover {
        border-color: var(--primary-blue);
        box-shadow: var(--shadow-md);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 2px solid var(--border-color);
    }
    
    section[data-testid="stSidebar"] > div {
        background: var(--bg-secondary) !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: var(--bg-secondary);
        border-radius: 8px;
        padding: 0.5rem;
        border: 1px solid var(--border-color);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px;
        color: var(--text-secondary) !important;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        border: 1px solid transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary-blue) !important;
        color: white !important;
        border-color: var(--primary-blue);
        box-shadow: var(--shadow-sm);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: var(--primary-blue) !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stMetricDelta"] {
        color: var(--success-green) !important;
    }
    
    /* DATAFRAMES */
    .dataframe {
        background: var(--bg-primary) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }
    
    .dataframe thead th {
        background: var(--bg-secondary) !important;
        color: var(--primary-blue) !important;
        font-weight: 700 !important;
        border-bottom: 2px solid var(--primary-blue) !important;
        padding: 12px 8px !important;
        text-align: left !important;
    }
    
    .dataframe tbody td {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        border-bottom: 1px solid var(--border-color) !important;
        padding: 10px 8px !important;
        font-weight: 500 !important;
    }
    
    .dataframe tbody tr:hover {
        background: var(--bg-tertiary) !important;
    }
    
    /* Streamlit dataframe viewer */
    [data-testid="stDataFrame"] {
        background: var(--bg-primary) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 8px;
        box-shadow: var(--shadow-sm);
    }
    
    [data-testid="stDataFrame"] * {
        color: var(--text-primary) !important;
    }
    
    /* Info/Warning/Error boxes */
    .stAlert {
        background: var(--bg-tertiary) !important;
        border-radius: 8px;
        border-left: 4px solid;
        color: var(--text-primary) !important;
        box-shadow: var(--shadow-sm);
    }
    
    .stSuccess {
        border-left-color: var(--success-green) !important;
        background: rgba(5, 150, 105, 0.1) !important;
    }
    
    .stWarning {
        border-left-color: var(--warning-yellow) !important;
        background: rgba(217, 119, 6, 0.1) !important;
    }
    
    .stError {
        border-left-color: var(--danger-red) !important;
        background: rgba(220, 38, 38, 0.1) !important;
    }
    
    .stInfo {
        border-left-color: var(--primary-blue) !important;
        background: rgba(37, 99, 235, 0.1) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-secondary) !important;
        border-radius: 8px;
        color: var(--text-primary) !important;
        border: 2px solid var(--border-color);
        font-weight: 600;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: var(--primary-blue);
        background: var(--bg-tertiary) !important;
    }
    
    /* Divider */
    hr {
        border-color: var(--border-color) !important;
        margin: 2rem 0;
    }
    
    /* Status badges */
    .status-success {
        color: var(--success-green) !important;
        font-weight: 600;
    }
    
    .status-warning {
        color: var(--warning-yellow) !important;
        font-weight: 600;
    }
    
    .status-error {
        color: var(--danger-red) !important;
        font-weight: 600;
    }
    
    /* Caption */
    .stCaption, caption {
        color: var(--text-muted) !important;
    }
    
    /* Suggestion box */
    .suggestion-box {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    /* SQL Query Box */
    .sql-box {
        background: var(--bg-secondary);
        border: 2px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
    }
    
    .sql-example {
        background: var(--bg-tertiary);
        border-left: 4px solid var(--primary-blue);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        color: var(--text-primary) !important;
    }
    
    /* Code blocks */
    code {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        .sub-header {
            font-size: 1.2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Popular NSE stocks for auto-suggestion
POPULAR_NSE_STOCKS = {
    "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "INDUSINDBK", "BANKBARODA"],
    "IT": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM", "COFORGE"],
    "Auto": ["TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO"],
    "Energy": ["RELIANCE", "ONGC", "POWERGRID", "NTPC", "COALINDIA", "ADANIGREEN"],
    "Pharma": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "AUROPHARMA", "LUPIN"],
    "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR", "MARICO"],
    "Metals": ["TATASTEEL", "HINDALCO", "JSWSTEEL", "VEDL", "COALINDIA", "NATIONALUM"],
    "Telecom": ["BHARTIARTL", "IDEA", "MTNL"],
    "Cement": ["ULTRACEMCO", "GRASIM", "SHREECEM", "AMBUJACEM", "ACC"],
    "Infra": ["LT", "DLF", "ADANIPORTS", "ADANIENT"]
}

# SQL Query Examples
SQL_EXAMPLES = {
    "All Companies": "SELECT * FROM companies LIMIT 10;",
    "Price History": "SELECT * FROM price_history WHERE symbol = 'INFY' ORDER BY date DESC LIMIT 10;",
    "Recent Updates": "SELECT symbol, MAX(date) as last_update FROM price_history GROUP BY symbol ORDER BY last_update DESC;",
    "Quarterly Results": "SELECT * FROM quarterly_results WHERE symbol = 'TCS' ORDER BY quarter DESC LIMIT 8;",
    "Annual Results": "SELECT * FROM annual_results WHERE symbol = 'RELIANCE' ORDER BY year DESC LIMIT 5;",
    "Shareholding": "SELECT * FROM shareholding WHERE symbol = 'HDFCBANK' ORDER BY quarter DESC LIMIT 4;",
    "Price Range": "SELECT symbol, MIN(low) as min_price, MAX(high) as max_price, AVG(close) as avg_price FROM price_history WHERE date >= date('now', '-1 year') GROUP BY symbol;",
    "Volume Analysis": "SELECT symbol, AVG(volume) as avg_volume, MAX(volume) as max_volume FROM price_history WHERE date >= date('now', '-30 days') GROUP BY symbol ORDER BY avg_volume DESC;",
    "Table Info": "SELECT name FROM sqlite_master WHERE type='table';",
    "Table Schema": "PRAGMA table_info(price_history);"
}

# Initialize
@st.cache_resource
def get_database():
    """Get database connection (cached)."""
    return DatabaseManager()

@st.cache_resource
def get_updater():
    """Get data updater (cached)."""
    return DataUpdater()

@st.cache_resource
def get_nse():
    """Get NSE data source (cached)."""
    return NSEComplete()

db = get_database()
updater = get_updater()
nse = get_nse()

# Helper functions
def validate_nse_symbol(symbol: str) -> bool:
    """Validate if symbol exists in NSE."""
    try:
        price_data = nse.get_price_data(symbol)
        return price_data is not None and 'last_price' in price_data
    except:
        return False

def download_historical_data(symbol: str, period: str, interval: str):
    """Download historical data from NSE."""
    try:
        df = nse.get_historical_prices(symbol, period=period, interval=interval)
        return df
    except Exception as e:
        st.error(f"Error downloading data: {e}")
        return None

def download_intraday_data(symbol: str, interval: str):
    """Download intraday data from NSE."""
    try:
        df = nse.get_intraday_data(symbol, interval=interval)
        return df
    except Exception as e:
        st.error(f"Error downloading intraday data: {e}")
        return None

def convert_df_to_csv(df):
    """Convert DataFrame to CSV."""
    return df.to_csv(index=True).encode('utf-8')

def convert_df_to_excel(df):
    """Convert DataFrame to Excel."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=True, sheet_name='Data')
    return output.getvalue()

def get_all_suggestions():
    """Get all popular stocks as flat list."""
    all_stocks = []
    for sector, stocks in POPULAR_NSE_STOCKS.items():
        all_stocks.extend(stocks)
    return sorted(set(all_stocks))

def execute_sql_query(query: str, db_path: str = None):
    """Execute SQL query and return results."""
    try:
        # Get database path
        if db_path is None:
            db_path = db.db_path
        
        # Security check - prevent destructive operations
        query_upper = query.upper().strip()
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'UPDATE', 'INSERT']
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return None, f"❌ {keyword} operations are not allowed for safety reasons"
        
        # Execute query
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df, None
    except Exception as e:
        return None, f"❌ Error: {str(e)}"

# Sidebar
with st.sidebar:
    st.markdown("### 📊 Fortune Trading")
    st.markdown("---")
    
    # Add new stock section
    with st.expander("➕ Add New Stock", expanded=False):
        st.markdown("**Popular Stocks:**")
        
        sector = st.selectbox("Select Sector", ["Type manually", "Banking", "IT", "Auto", "Energy", "Pharma", "FMCG", "Metals", "Telecom", "Cement", "Infra"])
        
        if sector != "Type manually":
            suggested_stocks = POPULAR_NSE_STOCKS.get(sector, [])
            selected_stock = st.selectbox("Choose Stock", suggested_stocks)
            new_symbol = selected_stock
        else:
            new_symbol = st.text_input(
                "Stock Symbol",
                placeholder="e.g., INFY, RELIANCE, HDFCBANK",
                help="Enter NSE stock symbol"
            ).upper().strip()
            
            if new_symbol and len(new_symbol) >= 2:
                all_stocks = get_all_suggestions()
                matching = [s for s in all_stocks if new_symbol in s]
                if matching:
                    st.markdown('<div class="suggestion-box">', unsafe_allow_html=True)
                    st.caption(f"💡 Suggestions: {', '.join(matching[:10])}")
                    st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("✓ Validate & Add", width='stretch'):
            if new_symbol:
                with st.spinner(f"Validating {new_symbol}..."):
                    if validate_nse_symbol(new_symbol):
                        with st.spinner(f"Adding {new_symbol}..."):
                            db.add_company(new_symbol, company_name=new_symbol)
                            result = updater.update_stock(new_symbol, force=True)
                            
                            if result.get('success'):
                                st.success(f"✅ {new_symbol} added successfully!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to update {new_symbol}")
                                errors = result.get('errors', [])
                                if errors:
                                    st.error(f"Errors: {errors[0]}")
                    else:
                        st.error(f"❌ Invalid symbol: {new_symbol}")
                        st.warning("Please check the symbol on NSE website")
            else:
                st.warning("Please enter a symbol")
    
    st.markdown("---")
    
    # Stock selector
    companies = db.get_all_companies()
    
    if not companies:
        st.warning("⚠️ No stocks in database")
        st.info("👆 Add a stock using the section above")
        selected_symbol = None
    else:
        symbols = sorted([c['symbol'] for c in companies])
        
        search_symbol = st.text_input("🔍 Search Stock", placeholder="Type to search...")
        
        if search_symbol:
            filtered_symbols = [s for s in symbols if search_symbol.upper() in s]
        else:
            filtered_symbols = symbols
        
        if filtered_symbols:
            selected_symbol = st.selectbox(
                "Select Stock",
                filtered_symbols,
                index=0,
                label_visibility="collapsed"
            )
        else:
            st.error("No matching stocks found")
            selected_symbol = None
    
    if selected_symbol:
        st.markdown("---")
        
        # Quick stats
        st.markdown("### 📈 Quick Stats")
        snapshot = db.get_snapshot(selected_symbol)
        
        if snapshot:
            price = snapshot.get('current_price', 0)
            change_pct = snapshot.get('change_percent', 0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Price", f"₹{price:,.0f}" if price else "N/A")
            with col2:
                if change_pct:
                    st.metric("Change", f"{change_pct:+.2f}%")
            
            st.metric("Market Cap", snapshot.get('market_cap', 'N/A'))
            st.metric("P/E", f"{snapshot.get('pe_ratio', 0):.1f}" if snapshot.get('pe_ratio') else "N/A")
        else:
            st.info("Update stock to see stats")
        
        st.markdown("---")
        
        # Update controls
        st.markdown("### 🔄 Data Update")
        
        last_update = db.get_last_update(selected_symbol)
        if last_update:
            age = datetime.now() - last_update
            hours_old = age.total_seconds() / 3600
            
            if hours_old < 1:
                st.markdown(f'<p class="status-success">✅ Updated {int(age.total_seconds() / 60)}m ago</p>', 
                           unsafe_allow_html=True)
            elif hours_old < 24:
                st.markdown(f'<p class="status-warning">⏰ {int(hours_old)}h ago</p>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<p class="status-error">⚠️ {int(hours_old / 24)}d ago</p>', 
                           unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-error">❌ Never updated</p>', unsafe_allow_html=True)
        
        if st.button("🔄 Update Data", width='stretch'):
            with st.spinner(f"Updating {selected_symbol}..."):
                result = updater.update_stock(selected_symbol, force=True)
                if result.get('success'):
                    st.success("✅ Success!")
                    st.rerun()
                else:
                    st.error("❌ Failed")
    
    st.markdown("---")
    
    # Database stats
    with st.expander("📊 Database Info"):
        stats = db.get_database_stats()
        st.metric("DB Size", f"{stats['database_size']:.2f} MB")
        st.metric("Companies", len(companies) if companies else 0)
        st.metric("Records", f"{stats['table_counts'].get('price_history', 0):,}")

# Main content
if selected_symbol:
    st.markdown(f'<div class="main-header">📈 {selected_symbol}</div>', unsafe_allow_html=True)
    
    # Get data
    company = db.get_company(selected_symbol)
    price_history = db.get_price_history(selected_symbol, days=7300)
    quarterly = db.get_quarterly_results(selected_symbol, limit=8)
    annual = db.get_annual_results(selected_symbol, limit=10)
    shareholding = db.get_shareholding(selected_symbol, limit=8)
    peers = db.get_peers(selected_symbol)
else:
    st.markdown('<div class="main-header">📊 Fortune Trading Dashboard</div>', unsafe_allow_html=True)
    st.info("👈 Please select or add a stock from the sidebar to begin")
    price_history = pd.DataFrame()
    quarterly = pd.DataFrame()
    annual = pd.DataFrame()
    shareholding = pd.DataFrame()
    peers = pd.DataFrame()
    snapshot = None
    company = None

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Overview", 
    "📈 Charts", 
    "💰 Financials", 
    "🏢 Peers", 
    "📥 Download",
    "🔍 SQL Query",
    "⚙️ Settings"
])

# Chart theme - Light
chart_theme = {
    'template': 'plotly_white',
    'paper_bgcolor': 'rgba(255, 255, 255, 0.9)',
    'plot_bgcolor': 'rgba(249, 250, 251, 0.5)',
    'font': {'color': '#111827', 'family': 'Arial, sans-serif'}
}

# TAB 1: Overview
with tab1:
    if not selected_symbol:
        st.info("Select a stock from sidebar to view overview")
    elif snapshot:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        price = snapshot.get('current_price', 0)
        change_pct = snapshot.get('change_percent', 0)
        
        with col1:
            st.metric("Price", f"₹{price:,.2f}" if price else "N/A", 
                     f"{change_pct:+.2f}%" if change_pct else None)
        with col2:
            st.metric("Market Cap", snapshot.get('market_cap', 'N/A'))
        with col3:
            st.metric("P/E", f"{snapshot.get('pe_ratio', 0):.2f}" if snapshot.get('pe_ratio') else "N/A")
        with col4:
            st.metric("ROE", f"{snapshot.get('roe', 0):.1f}%" if snapshot.get('roe') else "N/A")
        with col5:
            st.metric("ROCE", f"{snapshot.get('roce', 0):.1f}%" if snapshot.get('roce') else "N/A")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("52W High", f"₹{snapshot.get('high_52w', 0):,.2f}" if snapshot.get('high_52w') else "N/A")
        with col2:
            st.metric("52W Low", f"₹{snapshot.get('low_52w', 0):,.2f}" if snapshot.get('low_52w') else "N/A")
        with col3:
            st.metric("Book Value", f"₹{snapshot.get('book_value', 0):,.2f}" if snapshot.get('book_value') else "N/A")
        with col4:
            st.metric("Div Yield", f"{snapshot.get('dividend_yield', 0):.2f}%" if snapshot.get('dividend_yield') else "N/A")
    else:
        st.info("📊 No data available. Click '🔄 Update Data' in sidebar to fetch.")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<p class="sub-header">📊 Quarterly Performance</p>', unsafe_allow_html=True)
        if not quarterly.empty:
            recent_q = quarterly.head(4)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=recent_q['quarter'], y=recent_q['sales'], 
                                name='Sales', marker_color='#2563EB'))
            fig.add_trace(go.Bar(x=recent_q['quarter'], y=recent_q['net_profit'], 
                                name='Profit', marker_color='#059669'))
            
            fig.update_layout(barmode='group', height=350, margin=dict(l=0, r=0, t=30, b=0), **chart_theme)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No quarterly data")
    
    with col2:
        st.markdown('<p class="sub-header">👥 Shareholding</p>', unsafe_allow_html=True)
        if not shareholding.empty:
            latest = shareholding.iloc[0]
            
            labels, values = [], []
            colors = ['#2563EB', '#059669', '#EA580C', '#7C3AED', '#D97706']
            
            for holder in ['promoters', 'fii', 'dii', 'public', 'government']:
                val = latest.get(holder)
                if val and val > 0:
                    labels.append(holder.upper())
                    values.append(val)
            
            if values:
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.5, 
                                            marker_colors=colors[:len(labels)])])
                fig.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0), 
                                showlegend=True, **chart_theme)
                st.plotly_chart(fig, width='stretch')
        else:
            st.info("No shareholding data")

# TAB 2: Charts
with tab2:
    st.markdown('<p class="sub-header">📈 Price History</p>', unsafe_allow_html=True)
    
    if not selected_symbol:
        st.info("Select a stock from sidebar to view charts")
    elif not price_history.empty:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            period = st.selectbox("Period", 
                ["1W", "1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y", "ALL"], index=4)
        with col2:
            chart_type = st.selectbox("Type", ["Candlestick", "Line", "Area"])
        with col3:
            show_volume = st.checkbox("Volume", value=True)
        
        # Filter
        today = datetime.now()
        period_map = {
            "1W": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365, 
            "2Y": 730, "5Y": 1825, "10Y": 3650
        }
        
        if period in period_map:
            start_date = today - timedelta(days=period_map[period])
            filtered_df = price_history[price_history['date'] >= start_date]
        else:
            filtered_df = price_history
        
        if filtered_df.empty:
            st.warning(f"⚠️ No data for {period} period. Try downloading historical data from 'Download' tab.")
        else:
            # Chart
            fig = go.Figure()
            
            if chart_type == "Candlestick":
                fig.add_trace(go.Candlestick(
                    x=filtered_df['date'], 
                    open=filtered_df['open'], 
                    high=filtered_df['high'], 
                    low=filtered_df['low'], 
                    close=filtered_df['close'], 
                    name=selected_symbol,
                    increasing_line_color='#059669', 
                    decreasing_line_color='#DC2626'
                ))
            elif chart_type == "Line":
                fig.add_trace(go.Scatter(
                    x=filtered_df['date'], 
                    y=filtered_df['close'], 
                    mode='lines', 
                    line=dict(color='#2563EB', width=2),
                    name='Close'
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=filtered_df['date'], 
                    y=filtered_df['close'], 
                    mode='lines', 
                    fill='tozeroy', 
                    line=dict(color='#2563EB', width=2),
                    fillcolor='rgba(37, 99, 235, 0.2)',
                    name='Close'
                ))
            
            fig.update_layout(
                title=f"{selected_symbol} - {period} ({len(filtered_df)} records)", 
                height=500, 
                hovermode='x unified', 
                xaxis_rangeslider_visible=False,
                xaxis=dict(gridcolor='#E5E7EB'),
                yaxis=dict(gridcolor='#E5E7EB'),
                **chart_theme
            )
            st.plotly_chart(fig, width='stretch')
            
            # Volume
            if show_volume:
                fig_vol = go.Figure()
                fig_vol.add_trace(go.Bar(
                    x=filtered_df['date'], 
                    y=filtered_df['volume'], 
                    marker_color='#2563EB', 
                    opacity=0.6,
                    name='Volume'
                ))
                fig_vol.update_layout(
                    height=200, 
                    margin=dict(l=0, r=0, t=10, b=0), 
                    yaxis_title="Volume",
                    xaxis=dict(gridcolor='#E5E7EB'),
                    yaxis=dict(gridcolor='#E5E7EB'),
                    **chart_theme
                )
                st.plotly_chart(fig_vol, width='stretch')
            
            # Stats
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Records", f"{len(filtered_df):,}")
            with col2:
                st.metric("High", f"₹{filtered_df['high'].max():,.2f}")
            with col3:
                st.metric("Low", f"₹{filtered_df['low'].min():,.2f}")
            with col4:
                st.metric("Avg Vol", f"{filtered_df['volume'].mean():,.0f}")
            with col5:
                if len(filtered_df) > 1:
                    returns = ((filtered_df['close'].iloc[-1] / filtered_df['close'].iloc[0]) - 1) * 100
                    st.metric("Returns", f"{returns:+.2f}%")
    else:
        st.warning("📊 No price history in database")
        st.info("👉 Go to 'Download' tab to fetch historical data")

# TAB 3: Financials
with tab3:
    if not selected_symbol:
        st.info("Select a stock from sidebar to view financials")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<p class="sub-header">📊 Quarterly</p>', unsafe_allow_html=True)
            if not quarterly.empty:
                display_df = quarterly[['quarter', 'sales', 'net_profit', 'eps']].head(8).copy()
                display_df['sales'] = display_df['sales'].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) else "N/A")
                display_df['net_profit'] = display_df['net_profit'].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) else "N/A")
                display_df['eps'] = display_df['eps'].apply(lambda x: f"₹{x:.2f}" if pd.notnull(x) else "N/A")
                
                st.dataframe(display_df, width='stretch', hide_index=True)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=quarterly['quarter'], 
                    y=quarterly['sales'], 
                    mode='lines+markers', 
                    line=dict(color='#2563EB', width=3),
                    marker=dict(size=8),
                    name='Sales'
                ))
                fig.update_layout(
                    title="Sales Trend", 
                    height=300,
                    xaxis=dict(gridcolor='#E5E7EB'),
                    yaxis=dict(gridcolor='#E5E7EB'),
                    **chart_theme
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("No data")
        
        with col2:
            st.markdown('<p class="sub-header">📈 Annual</p>', unsafe_allow_html=True)
            if not annual.empty:
                display_df = annual[['year', 'sales', 'net_profit', 'eps']].head(10).copy()
                display_df['sales'] = display_df['sales'].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) else "N/A")
                display_df['net_profit'] = display_df['net_profit'].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) else "N/A")
                display_df['eps'] = display_df['eps'].apply(lambda x: f"₹{x:.2f}" if pd.notnull(x) else "N/A")
                
                st.dataframe(display_df, width='stretch', hide_index=True)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=annual['year'], 
                    y=annual['net_profit'], 
                    mode='lines+markers', 
                    fill='tozeroy',
                    line=dict(color='#059669', width=3),
                    fillcolor='rgba(5, 150, 105, 0.2)',
                    marker=dict(size=8),
                    name='Profit'
                ))
                fig.update_layout(
                    title="Profit Trend", 
                    height=300,
                    xaxis=dict(gridcolor='#E5E7EB'),
                    yaxis=dict(gridcolor='#E5E7EB'),
                    **chart_theme
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("No data")

# TAB 4: Peers
with tab4:
    st.markdown('<p class="sub-header">🏢 Peer Comparison</p>', unsafe_allow_html=True)
    
    if not selected_symbol:
        st.info("Select a stock from sidebar to view peer comparison")
    elif not peers.empty:
        display_df = peers[['peer_name', 'cmp', 'pe', 'market_cap', 'roe', 'roce']].copy()
        st.dataframe(display_df, width='stretch', hide_index=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                pe_data = pd.to_numeric(peers['pe'], errors='coerce')
                valid_pe = pe_data.notna() & (pe_data > 0)
                
                if valid_pe.sum() > 0:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=peers.loc[valid_pe, 'peer_name'], 
                        y=pe_data[valid_pe], 
                        marker_color='#2563EB',
                        text=[f"{v:.1f}" for v in pe_data[valid_pe]],
                        textposition='outside',
                        textfont=dict(color='#111827')
                    ))
                    fig.update_layout(
                        title="P/E Comparison", 
                        height=400, 
                        xaxis_tickangle=-45,
                        xaxis=dict(gridcolor='#E5E7EB'),
                        yaxis=dict(gridcolor='#E5E7EB', title='P/E'),
                        **chart_theme
                    )
                    st.plotly_chart(fig, width='stretch')
                else:
                    st.info("No valid P/E data")
            except Exception as e:
                st.error(f"Error displaying P/E chart: {e}")
        
        with col2:
            try:
                roe_data = pd.to_numeric(peers['roe'], errors='coerce')
                valid_roe = roe_data.notna() & (roe_data != 0)
                
                if valid_roe.sum() > 0:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=peers.loc[valid_roe, 'peer_name'], 
                        y=roe_data[valid_roe], 
                        marker_color='#059669',
                        text=[f"{v:.1f}" for v in roe_data[valid_roe]],
                        textposition='outside',
                        textfont=dict(color='#111827')
                    ))
                    fig.update_layout(
                        title="ROE Comparison", 
                        height=400, 
                        xaxis_tickangle=-45,
                        xaxis=dict(gridcolor='#E5E7EB'),
                        yaxis=dict(gridcolor='#E5E7EB', title='ROE %'),
                        **chart_theme
                    )
                    st.plotly_chart(fig, width='stretch')
                else:
                    st.info("No valid ROE data")
            except Exception as e:
                st.error(f"Error displaying ROE chart: {e}")
    else:
        st.info("No peer data available")

# TAB 5: Download
with tab5:
    if not selected_symbol:
        st.info("Select a stock from sidebar to download data")
    else:
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">📥 Download Historical Data</p>', unsafe_allow_html=True)
        st.write("Download OHLC data from NSE (since 1990 or earliest available)")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.write("")
        
        download_type = st.radio("Data Type", 
            ["📊 Historical (Since 1990)", "⚡ Intraday (Today)"], horizontal=True)
        
        if download_type == "📊 Historical (Since 1990)":
            st.markdown("### Historical OHLC Data")
            st.info("💡 'max' period downloads from Jan 1, 1990 or earliest available date")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                period = st.selectbox("Period", 
                    ["max", "20y", "10y", "5y", "2y", "1y", "6m", "3m", "1m"], index=0)
            with col2:
                interval = st.selectbox("Interval", ["1d", "1w", "1M"], index=0)
            with col3:
                st.write("")
                st.write("")
                save_to_db = st.checkbox("💾 Save", value=True)
            
            if st.button("📥 Download", width='stretch', type="primary"):
                with st.spinner(f"Downloading {interval} data (period: {period})..."):
                    df = download_historical_data(selected_symbol, period, interval)
                    
                    if df is not None and not df.empty:
                        st.success(f"✅ Downloaded {len(df)} records")
                        
                        if save_to_db:
                            db.save_price_history(selected_symbol, df)
                            st.success("✅ Saved to database")
                            st.info("🔄 Refresh the page to see updated charts")
                        
                        st.session_state['downloaded_df'] = df
                        st.session_state['download_filename'] = f"{selected_symbol}_{interval}_{period}"
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Records", len(df))
                        with col2:
                            st.metric("From", df.index.min().strftime('%Y-%m-%d') if hasattr(df.index, 'min') else "N/A")
                        with col3:
                            st.metric("To", df.index.max().strftime('%Y-%m-%d') if hasattr(df.index, 'max') else "N/A")
                        with col4:
                            st.metric("Interval", interval.upper())
                        
                        st.markdown("#### Preview:")
                        st.dataframe(df.head(10), width='stretch')
                    else:
                        st.error("❌ No data received")
        
        else:
            st.markdown("### ⚡ Intraday Data")
            st.warning("⏰ Available only during market hours")
            
            intraday_interval = st.selectbox("Interval", 
                ["1m", "3m", "5m", "10m", "15m", "30m", "1h"], index=2)
            
            if st.button("📥 Download Intraday", width='stretch', type="primary"):
                with st.spinner("Downloading..."):
                    df = download_intraday_data(selected_symbol, intraday_interval)
                    
                    if df is not None and not df.empty:
                        st.success(f"✅ {len(df)} records")
                        st.session_state['downloaded_df'] = df
                        st.session_state['download_filename'] = f"{selected_symbol}_intraday_{intraday_interval}"
                        st.dataframe(df.head(10), width='stretch')
                    else:
                        st.error("❌ No data - Market closed?")
        
        # Export
        if 'downloaded_df' in st.session_state:
            st.markdown("---")
            st.markdown("### 💾 Export")
            
            df_to_export = st.session_state['downloaded_df']
            filename = st.session_state['download_filename']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button("📄 CSV", convert_df_to_csv(df_to_export), 
                                 f"{filename}.csv", "text/csv", width='stretch')
            with col2:
                st.download_button("📊 Excel", convert_df_to_excel(df_to_export), 
                                 f"{filename}.xlsx", width='stretch')
            with col3:
                st.metric("Rows", len(df_to_export))

# TAB 6: SQL Query - NEW!
with tab6:
    st.markdown('<div class="sql-box">', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">🔍 SQL Query Interface</p>', unsafe_allow_html=True)
    st.markdown("Execute custom SQL queries on the database (Read-only mode)")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📝 Query Editor")
        
        # Example selector
        example_query = st.selectbox(
            "Load Example Query:",
            ["Custom Query"] + list(SQL_EXAMPLES.keys())
        )
        
        if example_query != "Custom Query":
            default_query = SQL_EXAMPLES[example_query]
        else:
            default_query = "SELECT * FROM companies LIMIT 10;"
        
        # Query input
        sql_query = st.text_area(
            "SQL Query:",
            value=default_query,
            height=200,
            help="Enter your SQL query here. Only SELECT queries are allowed."
        )
        
        col_a, col_b, col_c = st.columns([1, 1, 2])
        with col_a:
            execute_btn = st.button("▶️ Execute", type="primary", width='stretch')
        with col_b:
            clear_btn = st.button("🗑️ Clear", width='stretch')
        
        if clear_btn:
            st.rerun()
    
    with col2:
        st.markdown("### 📚 Quick Reference")
        
        with st.expander("📋 Available Tables", expanded=True):
            st.markdown("""
            - `companies`
            - `price_history`
            - `quarterly_results`
            - `annual_results`
            - `shareholding`
            - `peers`
            """)
        
        with st.expander("💡 Tips"):
            st.markdown("""
            - Use `LIMIT` to restrict results
            - Only SELECT queries allowed
            - Table names are case-sensitive
            - Use date('now') for current date
            - Example: `WHERE date >= date('now', '-30 days')`
            """)
        
        with st.expander("⚠️ Safety"):
            st.markdown("""
            **Read-Only Mode:**
            - ❌ DROP not allowed
            - ❌ DELETE not allowed
            - ❌ UPDATE not allowed
            - ❌ INSERT not allowed
            - ✅ SELECT only
            """)
    
    # Execute query
    if execute_btn:
        if not sql_query.strip():
            st.warning("⚠️ Please enter a SQL query")
        else:
            with st.spinner("Executing query..."):
                result_df, error = execute_sql_query(sql_query)
                
                if error:
                    st.error(error)
                elif result_df is not None:
                    if result_df.empty:
                        st.info("✅ Query executed successfully. No results returned.")
                    else:
                        st.success(f"✅ Query executed successfully! {len(result_df)} rows returned")
                        
                        # Display results
                        st.markdown("### 📊 Results")
                        
                        # Metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Rows", len(result_df))
                        with col2:
                            st.metric("Columns", len(result_df.columns))
                        with col3:
                            st.metric("Memory", f"{result_df.memory_usage(deep=True).sum() / 1024:.1f} KB")
                        
                        # Data table
                        st.dataframe(result_df, width='stretch', height=400)
                        
                        # Export options
                        st.markdown("### 💾 Export Results")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.download_button(
                                "📄 Download CSV",
                                convert_df_to_csv(result_df),
                                "query_results.csv",
                                "text/csv",
                                width='stretch'
                            )
                        with col2:
                            st.download_button(
                                "📊 Download Excel",
                                convert_df_to_excel(result_df),
                                "query_results.xlsx",
                                width='stretch'
                            )
                        with col3:
                            st.code(sql_query, language="sql")
    
    # Example queries section
    st.markdown("---")
    st.markdown("### 📖 Example Queries")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Basic Queries")
        for name, query in list(SQL_EXAMPLES.items())[:5]:
            with st.expander(f"📌 {name}"):
                st.code(query, language="sql")
    
    with col2:
        st.markdown("#### Advanced Queries")
        for name, query in list(SQL_EXAMPLES.items())[5:]:
            with st.expander(f"📌 {name}"):
                st.code(query, language="sql")

# TAB 7: Settings
with tab6:
    st.markdown('<p class="sub-header">⚙️ Settings</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Company Details")
        if selected_symbol and company:
            st.write("**Symbol:**", company.get('symbol'))
            st.write("**Name:**", company.get('company_name'))
            st.write("**Sector:**", company.get('sector', 'N/A'))
            st.write("**ISIN:**", company.get('isin', 'N/A'))
        else:
            st.info("Select a stock to view details")
    
    with col2:
        st.markdown("### 🗄️ Database Management")
        if st.button("🔄 Optimize Database"):
            with st.spinner("Optimizing..."):
                db.vacuum()
                st.success("✅ Database optimized")
        
        if st.button("🔄 Refresh Dashboard"):
            st.rerun()
        
        st.markdown("---")
        st.markdown("**Database Path:**")
        st.code(str(db.db_path), language="text")

# Footer
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: var(--text-muted); font-size: 0.9rem;">'
    '⚡ Fortune Trading v2.0 | Professional Light Theme | NSE Real-time Data | SQL Query Interface'
    '</p>', 
    unsafe_allow_html=True
)