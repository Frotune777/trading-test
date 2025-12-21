# dashboard/pages/research.py
"""
Research Page - Stock screening and analysis
Version: 3.0 - Production Ready
"""

import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime
from typing import List, Optional

from frontend.utils.data_loader import get_database
from backend.app.services.data_aggregator import HybridAggregator


def research_page():
    """Research and screening dashboard"""
    st.markdown("## 🔍 Research & Screening")
    
    tab1, tab2, tab3 = st.tabs(["🎯 Stock Screener", "📊 Sector Analysis", "🔬 Custom Research"])
    
    with tab1:
        screener_tab()
    
    with tab2:
        sector_analysis_tab()
    
    with tab3:
        custom_research_tab()


def screener_tab():
    """Stock screener"""
    st.markdown('<p class="section-header">🎯 Stock Screener</p>', unsafe_allow_html=True)
    
    db = get_database()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**1️⃣ Select Universe**")
        
        preset_lists = {
            "NIFTY 50": ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "HINDUNILVR"],
            "IT Sector": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM"],
            "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"],
            "All Stocks in DB": [],
            "Custom": []
        }
        
        universe = st.selectbox("Universe", list(preset_lists.keys()))
        
        if universe == "All Stocks in DB":
            companies = db.get_all_companies()
            symbols = [c['symbol'] for c in companies]
            st.info(f"📊 {len(symbols)} stocks")
        elif universe == "Custom":
            custom_input = st.text_area("Symbols (one per line)")
            symbols = [s.strip().upper() for s in re.split('[,\n]', custom_input) if s.strip()]
        else:
            symbols = preset_lists[universe]
            st.info(f"📊 {len(symbols)} stocks")
    
    with col2:
        st.markdown("**2️⃣ Filters**")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("*Profitability*")
            min_roe = st.number_input("Min ROE %", 0.0, 100.0, 15.0, 1.0)
            min_roce = st.number_input("Min ROCE %", 0.0, 100.0, 15.0, 1.0)
        
        with col_b:
            st.markdown("*Valuation*")
            max_pe = st.number_input("Max P/E", 0.0, 200.0, 30.0, 1.0)
            min_div_yield = st.number_input("Min Div Yield %", 0.0, 20.0, 1.0, 0.1)
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    if st.button("🔍 Run Screener", type="primary", width='stretch'):
        if not symbols:
            st.error("❌ Select stocks")
        else:
            run_screener(symbols, min_roe, max_pe, min_roce, min_div_yield)


def run_screener(symbols: List[str], min_roe: float, max_pe: float, min_roce: float, min_div_yield: float):
    """Execute screening"""
    aggregator = HybridAggregator()
    
    st.markdown('<p class="section-header">📊 Results</p>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, symbol in enumerate(symbols):
        status_text.text(f"Analyzing {i+1}/{len(symbols)}: {symbol}")
        
        try:
            data = aggregator.get_fundamental_data(symbol)
            
            if not data or not data.get('key_metrics'):
                continue
            
            metrics = data['key_metrics']
            
            roe = extract_number(metrics.get('ROE', '0'))
            pe = extract_number(metrics.get('Stock P/E', '999'))
            roce = extract_number(metrics.get('ROCE', '0'))
            div_yield = extract_number(metrics.get('Dividend Yield', '0'))
            
            if (roe >= min_roe and pe <= max_pe and roce >= min_roce and div_yield >= min_div_yield):
                results.append({
                    'Symbol': symbol,
                    'Company': data.get('company_info', {}).get('company_name', symbol),
                    'Sector': data.get('company_info', {}).get('sector', 'N/A'),
                    'Market Cap': metrics.get('Market Cap', 'N/A'),
                    'P/E': f"{pe:.2f}",
                    'ROE %': f"{roe:.2f}",
                    'ROCE %': f"{roce:.2f}",
                    'Div Yield %': f"{div_yield:.2f}"
                })
        except Exception as e:
            st.warning(f"⚠️ {symbol}: {e}")
        
        progress_bar.progress((i + 1) / len(symbols))
        time.sleep(0.5)
    
    progress_bar.empty()
    status_text.empty()
    
    if results:
        st.success(f"✅ Found {len(results)} stocks")
        df = pd.DataFrame(results).sort_values('ROE %', ascending=False)
        st.dataframe(df, width='stretch', hide_index=True)
        
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            f"screened_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            width='stretch'
        )
    else:
        st.warning("😔 No matches")


def sector_analysis_tab():
    """Sector analysis"""
    st.markdown('<p class="section-header">📊 Sector Analysis</p>', unsafe_allow_html=True)
    
    db = get_database()
    companies = db.get_all_companies()
    sectors = db.get_sectors()
    
    if not sectors:
        st.info("📊 No sectors")
        return
    
    selected_sector = st.selectbox("Sector", sectors)
    sector_companies = [c for c in companies if c.get('sector') == selected_sector]
    
    st.metric("Companies", len(sector_companies))
    
    if sector_companies:
        symbols_df = pd.DataFrame(sector_companies)[['symbol', 'company_name', 'sector']]
        st.dataframe(symbols_df, width='stretch', hide_index=True)


def custom_research_tab():
    """Custom tools"""
    st.markdown('<p class="section-header">🔬 Custom Tools</p>', unsafe_allow_html=True)
    
    tool = st.selectbox("Tool", ["Compare Stocks", "Historical", "Correlation", "Momentum"])
    
    if tool == "Compare Stocks":
        st.markdown("### 📊 Comparison")
        symbols_input = st.text_input("Symbols (comma separated)", "TCS, INFY")
        symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
        
        if len(symbols) >= 2 and st.button("Compare"):
            compare_stocks(symbols)
            
    elif tool == "Historical":
        st.markdown("### 📅 Historical Data")
        db = get_database()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            companies = db.get_all_companies()
            symbols = sorted([c['symbol'] for c in companies]) if companies else []
            symbol = st.selectbox("Select Stock", symbols) if symbols else st.text_input("Symbol")
            
        with col2:
            days = st.selectbox("Period", [30, 90, 180, 365, 730], index=3)
            
        if symbol:
            df = db.get_price_history(symbol, days=days)
            if not df.empty:
                st.dataframe(df, width='stretch', hide_index=True)
                
                csv = df.to_csv(index=False)
                st.download_button("📥 Download Filtered Data", csv, f"{symbol}_history_{days}d.csv", "text/csv")
            else:
                st.warning("No historical data found. Please update data in Analytics or Data Manager.")
                
    else:
        st.info("🚧 Coming soon")


def compare_stocks(symbols: List[str]):
    """Compare stocks"""
    db = get_database()
    comparison_data = []
    
    for symbol in symbols:
        snapshot = db.get_snapshot(symbol)
        company = db.get_company(symbol)
        
        if snapshot:
            comparison_data.append({
                'Symbol': symbol,
                'Company': company.get('company_name', symbol) if company else symbol,
                'Price': f"₹{snapshot.get('current_price', 0):,.2f}",
                'Change %': f"{snapshot.get('change_percent', 0):+.2f}%",
                'P/E': f"{snapshot.get('pe_ratio', 0):.2f}" if snapshot.get('pe_ratio') else 'N/A'
            })
    
    if comparison_data:
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, width='stretch', hide_index=True)
        
        csv = df.to_csv(index=False)
        st.download_button("📥 Download", csv, f"comparison_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
    else:
        st.warning("⚠️ No data")


def extract_number(value: str) -> float:
    """Extract number from string"""
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r'[₹,\s%]', '', str(value))
    try:
        return float(cleaned)
    except:
        return 0.0

if __name__ == "__main__":
    research_page()