# dashboard/pages/models.py
"""
Financial Models Page
Configure and export data for different model types
Prepare for TA-Lib integration
Version: 1.0
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json

from dashboard.utils.data_loader import get_database, get_nse
from core.model_data_prep import ModelDataPrep


def models_page():
    """Financial models configuration and data export"""
    
    st.markdown("## 🧮 Financial Models")
    
    st.info("""
    **Production-Ready Financial Analysis Framework**  
    Prepare data for machine learning models and quantitative strategies.  
    Next step: Add TA-Lib indicators for technical analysis.
    """)
    
    db = get_database()
    nse = get_nse()
    model_prep = ModelDataPrep(nse, db)
    
    # Model selection
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔴 Price Prediction",
        "🟠 Volatility Models",
        "🟠 Sentiment Analysis",
        "🟢 Event-Driven",
        "📊 Portfolio Optimization",
        "📈 Options Trading"
    ])
    
    with tab1:
        price_prediction_tab(model_prep, db)
    
    with tab2:
        volatility_models_tab(model_prep, db)
    
    with tab3:
        sentiment_analysis_tab(model_prep, db)
    
    with tab4:
        event_driven_tab(model_prep, db)
    
    with tab5:
        portfolio_optimization_tab(model_prep, db)
    
    with tab6:
        options_trading_tab(model_prep, db)


# ========================================================================
# TAB 1: PRICE PREDICTION
# ========================================================================

def price_prediction_tab(model_prep, db):
    """Price prediction model configuration"""
    
    st.markdown("### 🔴 Price Prediction Models")
    st.markdown("**Use Cases:** LSTM, ARIMA, Prophet, XGBoost for price forecasting")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        companies = db.get_all_companies()
        symbols = sorted([c['symbol'] for c in companies])
        
        if not symbols:
            st.error("❌ No stocks in database")
            return
        
        selected_symbol = st.selectbox("Select Stock", symbols)
        lookback_days = st.slider("Lookback Period (days)", 30, 730, 365)
    
    with col2:
        st.markdown("**Required Data:**")
        st.markdown("""
        ✅ Historical OHLCV  
        ✅ Company Fundamentals  
        ✅ Corporate Actions  
        ✅ FII/DII Activity  
        ✅ Market Indicators
        """)
    
    if st.button("📊 Prepare Data", type="primary", key="prep_price"):
        with st.spinner(f"Preparing data for {selected_symbol}..."):
            data = model_prep.prepare_price_prediction_data(selected_symbol, lookback_days)
            
            display_model_data(data, "price_prediction")


# ========================================================================
# TAB 2: VOLATILITY MODELS
# ========================================================================

def volatility_models_tab(model_prep, db):
    """Volatility modeling configuration"""
    
    st.markdown("### 🟠 Volatility Models")
    st.markdown("**Use Cases:** GARCH, Stochastic Volatility, Implied Vol Surface")
    
    companies = db.get_all_companies()
    symbols = sorted([c['symbol'] for c in companies])
    
    if not symbols:
        st.error("❌ No stocks in database")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_symbol = st.selectbox("Select Stock", symbols, key="vol_symbol")
        lookback_days = st.slider("Lookback (days)", 30, 365, 180, key="vol_days")
    
    with col2:
        st.markdown("**Required Data:**")
        st.markdown("""
        ✅ Option Chain (IV)  
        ✅ Futures Data  
        ✅ Historical Prices  
        ✅ Market Depth
        """)
    
    if st.button("📊 Prepare Data", type="primary", key="prep_vol"):
        with st.spinner(f"Preparing volatility data for {selected_symbol}..."):
            data = model_prep.prepare_volatility_model_data(selected_symbol, lookback_days)
            
            display_model_data(data, "volatility")


# ========================================================================
# TAB 3: SENTIMENT ANALYSIS
# ========================================================================

def sentiment_analysis_tab(model_prep, db):
    """Sentiment analysis configuration"""
    
    st.markdown("### 🟠 Sentiment Analysis")
    st.markdown("**Use Cases:** Market sentiment scoring, institutional activity tracking")
    
    companies = db.get_all_companies()
    symbols = sorted([c['symbol'] for c in companies])
    
    if not symbols:
        st.error("❌ No stocks in database")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_symbol = st.selectbox("Select Stock", symbols, key="sent_symbol")
        lookback_days = st.slider("Lookback (days)", 30, 180, 90, key="sent_days")
    
    with col2:
        st.markdown("**Required Data:**")
        st.markdown("""
        ✅ FII/DII Activity  
        ✅ Bulk Deals  
        ✅ Insider Trading  
        ✅ Gainers/Losers  
        ✅ Advance/Decline
        """)
    
    if st.button("📊 Prepare Data", type="primary", key="prep_sent"):
        with st.spinner(f"Preparing sentiment data for {selected_symbol}..."):
            data = model_prep.prepare_sentiment_data(selected_symbol, lookback_days)
            
            display_model_data(data, "sentiment")


# ========================================================================
# TAB 4: EVENT-DRIVEN
# ========================================================================

def event_driven_tab(model_prep, db):
    """Event-driven strategy configuration"""
    
    st.markdown("### 🟢 Event-Driven Strategies")
    st.markdown("**Use Cases:** Earnings plays, dividend strategies, corporate action trading")
    
    companies = db.get_all_companies()
    symbols = sorted([c['symbol'] for c in companies])
    
    if not symbols:
        st.error("❌ No stocks in database")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_symbol = st.selectbox("Select Stock", symbols, key="event_symbol")
        lookback_days = st.slider("Lookback (days)", 30, 365, 180, key="event_days")
    
    with col2:
        st.markdown("**Required Data:**")
        st.markdown("""
        ✅ Corporate Actions  
        ✅ Results Calendar  
        ✅ Announcements  
        ✅ Insider Trading  
        ✅ Price History
        """)
    
    if st.button("📊 Prepare Data", type="primary", key="prep_event"):
        with st.spinner(f"Preparing event data for {selected_symbol}..."):
            data = model_prep.prepare_event_driven_data(selected_symbol, lookback_days)
            
            display_model_data(data, "event_driven")


# ========================================================================
# TAB 5: PORTFOLIO OPTIMIZATION
# ========================================================================

def portfolio_optimization_tab(model_prep, db):
    """Portfolio optimization configuration"""
    
    st.markdown("### 📊 Portfolio Optimization")
    st.markdown("**Use Cases:** Markowitz, Black-Litterman, Risk Parity")
    
    companies = db.get_all_companies()
    sectors = list(set([c.get('sector') for c in companies if c.get('sector')]))
    
    if not companies:
        st.error("❌ No stocks in database")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Select Stocks for Portfolio:**")
        
        # Option 1: By sector
        use_sector = st.checkbox("Select by Sector")
        
        if use_sector:
            selected_sector = st.selectbox("Sector", sectors)
            symbols = [c['symbol'] for c in companies if c.get('sector') == selected_sector]
            st.info(f"📊 {len(symbols)} stocks in {selected_sector}")
        else:
            # Option 2: Manual selection
            all_symbols = sorted([c['symbol'] for c in companies])
            symbols = st.multiselect("Select Stocks", all_symbols, default=all_symbols[:5])
        
        lookback_days = st.slider("Lookback (days)", 90, 730, 365, key="port_days")
    
    with col2:
        st.markdown("**Required Data:**")
        st.markdown("""
        ✅ Historical Prices  
        ✅ Returns Matrix  
        ✅ Correlation  
        ✅ Company Info  
        ✅ Benchmark Data
        """)
    
    if symbols and st.button("📊 Prepare Data", type="primary", key="prep_port"):
        with st.spinner(f"Preparing portfolio data for {len(symbols)} stocks..."):
            data = model_prep.prepare_portfolio_data(symbols, lookback_days)
            
            display_model_data(data, "portfolio")


# ========================================================================
# TAB 6: OPTIONS TRADING
# ========================================================================

def options_trading_tab(model_prep, db):
    """Options trading configuration"""
    
    st.markdown("### 📈 Options Trading Strategies")
    st.markdown("**Use Cases:** Spread strategies, volatility trading, Greeks analysis")
    
    companies = db.get_all_companies()
    symbols = sorted([c['symbol'] for c in companies])
    
    if not symbols:
        st.error("❌ No stocks in database")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_symbol = st.selectbox("Select Stock", symbols, key="opt_symbol")
        expiry = st.text_input("Expiry Date (DD-MMM-YYYY)", placeholder="27-JUN-2025")
    
    with col2:
        st.markdown("**Required Data:**")
        st.markdown("""
        ✅ Live Option Chain  
        ✅ Historical Options  
        ✅ Underlying Prices  
        ✅ Most Active Options
        """)
    
    if st.button("📊 Prepare Data", type="primary", key="prep_opt"):
        with st.spinner(f"Preparing options data for {selected_symbol}..."):
            data = model_prep.prepare_options_trading_data(
                selected_symbol,
                expiry if expiry else None
            )
            
            display_model_data(data, "options")


# ========================================================================
# DATA DISPLAY FUNCTION
# ========================================================================

def display_model_data(data: dict, model_type: str):
    """Display prepared model data with quality assessment"""
    
    st.markdown("---")
    st.markdown("### 📊 Data Preparation Results")
    
    # Quality Score
    quality_score = data.get('quality_score', 0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Quality Score", f"{quality_score * 100:.0f}%")
    
    with col2:
        timestamp = data.get('timestamp', datetime.now())
        st.metric("Prepared At", timestamp.strftime("%H:%M:%S"))
    
    with col3:
        data_items = len(data.get('features', {}))
        st.metric("Data Items", data_items)
    
    # Quality breakdown
    st.markdown("**Data Quality Breakdown:**")
    
    quality_dict = data.get('data_quality', {})
    
    quality_df = pd.DataFrame([
        {
            'Data Source': source,
            'Status': '✅ OK' if status == 'OK' else '⚠️ No Data' if status == 'NO_DATA' else '❌ Missing' if status == 'MISSING' else '💥 Error',
            'Quality': status
        }
        for source, status in quality_dict.items()
    ])
    
    st.dataframe(quality_df, width='stretch', hide_index=True)
    
    # Show available features
    if data.get('features'):
        st.markdown("**Available Features:**")
        
        for feature_name, feature_data in data.get('features', {}).items():
            with st.expander(f"📊 {feature_name.replace('_', ' ').title()}"):
                if isinstance(feature_data, pd.DataFrame):
                    st.write(f"**Type:** DataFrame ({len(feature_data)} rows, {len(feature_data.columns)} columns)")
                    st.dataframe(feature_data.head(10), width='stretch')
                elif isinstance(feature_data, dict):
                    st.write(f"**Type:** Dictionary ({len(feature_data)} keys)")
                    st.json(feature_data)
                elif isinstance(feature_data, (pd.Series, list)):
                    st.write(f"**Type:** Series/List ({len(feature_data)} items)")
                    st.write(feature_data)
                else:
                    st.write(f"**Type:** {type(feature_data).__name__}")
                    st.write(feature_data)
    
    # Export options
    st.markdown("---")
    st.markdown("### 📥 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Export JSON", key=f"export_json_{model_type}"):
            # Convert to JSON-serializable format
            export_data = {
                'model_type': model_type,
                'timestamp': str(data.get('timestamp')),
                'quality_score': quality_score,
                'data_quality': quality_dict
            }
            
            json_str = json.dumps(export_data, indent=2, default=str)
            st.download_button(
                "💾 Download JSON",
                json_str,
                f"{model_type}_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json"
            )
    
    with col2:
        if st.button("📥 Export CSV", key=f"export_csv_{model_type}"):
            # Export features as CSV (if DataFrame available)
            for name, feat in data.get('features', {}).items():
                if isinstance(feat, pd.DataFrame):
                    csv = feat.to_csv(index=False)
                    st.download_button(
                        f"💾 Download {name}.csv",
                        csv,
                        f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
                    break
    
    with col3:
        st.info("**Next Step:**  \nAdd TA-Lib indicators  \nfor technical analysis")