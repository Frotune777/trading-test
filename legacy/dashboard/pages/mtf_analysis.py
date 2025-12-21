# dashboard/pages/mtf_analysis.py
"""
Multi-Timeframe Analysis Page
Visualize and analyze data across multiple timeframes
Version: 1.0
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

from dashboard.utils.data_loader import get_database, get_nse
from core.mtf_manager import MTFDataManager, TimeFrame


def mtf_analysis_page():
    """Multi-Timeframe Analysis Dashboard"""
    
    st.markdown("## 🕐 Multi-Timeframe Analysis")
    
    st.info("""
    **Professional Multi-Timeframe Trading Analysis**  
    Analyze price action, trends, and indicators across multiple timeframes simultaneously.  
    Essential for top-down analysis and trend confirmation.
    """)
    
    db = get_database()
    nse = get_nse()
    mtf_manager = MTFDataManager(db, nse)
    
    # Configuration
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        companies = db.get_all_companies()
        symbols = sorted([c['symbol'] for c in companies])
        
        if not symbols:
            st.error("❌ No stocks in database")
            return
        
        selected_symbol = st.selectbox("Select Stock", symbols)
    
    with col2:
        lookback_days = st.slider("Lookback Days", 7, 90, 30)
    
    with col3:
        chart_type = st.selectbox("Chart Type", ["Candlestick", "Line", "OHLC"])
    
    # Timeframe selection
    st.markdown("**Select Timeframes:**")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    selected_tfs = []
    
    with col1:
        if st.checkbox("📊 Daily", value=True):
            selected_tfs.append('1d')
    
    with col2:
        if st.checkbox("⏰ 4 Hour"):
            selected_tfs.append('4h')
    
    with col3:
        if st.checkbox("⏰ 1 Hour"):
            selected_tfs.append('1h')
    
    with col4:
        if st.checkbox("⏰ 15 Min"):
            selected_tfs.append('15m')
    
    with col5:
        if st.checkbox("⏰ 5 Min"):
            selected_tfs.append('5m')
    
    if not selected_tfs:
        st.warning("⚠️ Please select at least one timeframe")
        return
    
    # Fetch data
    if st.button("📊 Analyze", type="primary"):
        with st.spinner(f"Fetching multi-timeframe data for {selected_symbol}..."):
            mtf_data = mtf_manager.get_mtf_data(selected_symbol, selected_tfs, lookback_days)
            
            if not mtf_data:
                st.error("❌ No data available")
                return
            
            # Display analysis
            display_mtf_analysis(mtf_data, selected_symbol, chart_type, mtf_manager)


def display_mtf_analysis(
    mtf_data: dict,
    symbol: str,
    chart_type: str,
    mtf_manager: MTFDataManager
):
    """Display comprehensive MTF analysis"""
    
    st.markdown("---")
    st.markdown("### 📊 Multi-Timeframe Overview")
    
    # Trend alignment
    trends = mtf_manager.calculate_mtf_trend(mtf_data)
    
    st.markdown("**Trend Direction:**")
    
    cols = st.columns(len(trends))
    for i, (tf, trend) in enumerate(trends.items()):
        with cols[i]:
            if trend == 'UP':
                st.success(f"**{tf}**: 🟢 UP")
            elif trend == 'DOWN':
                st.error(f"**{tf}**: 🔴 DOWN")
            elif trend == 'NEUTRAL':
                st.warning(f"**{tf}**: 🟡 NEUTRAL")
            else:
                st.info(f"**{tf}**: ⚪ UNKNOWN")
    
    # Check alignment
    up_aligned = mtf_manager.is_mtf_aligned(mtf_data, 'UP', min_timeframes=2)
    down_aligned = mtf_manager.is_mtf_aligned(mtf_data, 'DOWN', min_timeframes=2)
    
    if up_aligned:
        st.success("✅ **Multi-Timeframe BULLISH Alignment Detected**")
    elif down_aligned:
        st.error("⚠️ **Multi-Timeframe BEARISH Alignment Detected**")
    else:
        st.info("ℹ️ **No clear multi-timeframe alignment**")
    
    st.markdown("---")
    
    # Data quality report
    quality_report = mtf_manager.validate_mtf_data(mtf_data)
    
    with st.expander("📊 Data Quality Report"):
        quality_df = pd.DataFrame([
            {
                'Timeframe': tf,
                'Bars': info['rows'],
                'Date Range': info['date_range'],
                'Quality Score': f"{info['quality_score']}%"
            }
            for tf, info in quality_report.items()
        ])
        
        st.dataframe(quality_df, width='stretch', hide_index=True)
    
    st.markdown("---")
    
    # Charts for each timeframe
    st.markdown("### 📈 Price Charts")
    
    for tf in sorted(mtf_data.keys(), key=lambda x: TimeFrame.get_minutes(x), reverse=True):
        render_timeframe_chart(mtf_data[tf], symbol, tf, chart_type, trends.get(tf))


def render_timeframe_chart(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    chart_type: str,
    trend: str
):
    """Render chart for single timeframe"""
    
    st.markdown(f"#### {timeframe.upper()} Chart")
    
    if df.empty:
        st.warning(f"No data for {timeframe}")
        return
    
    # Prepare data
    if 'date' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'])
    elif 'timestamp' in df.columns:
        df['datetime'] = pd.to_datetime(df['timestamp'])
    else:
        df['datetime'] = pd.to_datetime(df.index)
    
    # Create figure
    fig = go.Figure()
    
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df['datetime'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='OHLC',
            increasing_line_color='#2ecc71',
            decreasing_line_color='#e74c3c'
        ))
    elif chart_type == "OHLC":
        fig.add_trace(go.Ohlc(
            x=df['datetime'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='OHLC'
        ))
    else:  # Line
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['close'],
            name='Close',
            line=dict(color='#4a90e2', width=2)
        ))
    
    # Add MA
    if len(df) >= 20:
        df['ma20'] = df['close'].rolling(20).mean()
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['ma20'],
            name='MA20',
            line=dict(color='#f39c12', width=1.5),
            opacity=0.7
        ))
    
    # Trend color
    trend_color = '#2ecc71' if trend == 'UP' else '#e74c3c' if trend == 'DOWN' else '#f39c12'
    
    fig.update_layout(
        title=dict(
            text=f'{symbol} - {timeframe} | Trend: {trend}',
            font=dict(color='#e6edf3')
        ),
        xaxis=dict(
            gridcolor='#2d3748',
            color='#e6edf3'
        ),
        yaxis=dict(
            gridcolor='#2d3748',
            color='#e6edf3'
        ),
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        font=dict(color='#e6edf3'),
        showlegend=True,
        legend=dict(font=dict(color='#e6edf3'))
    )
    
    st.plotly_chart(fig, width='stretch')
    
    # Key stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Bars", len(df))
    
    with col2:
        high = df['high'].max()
        st.metric("High", f"₹{high:,.2f}")
    
    with col3:
        low = df['low'].min()
        st.metric("Low", f"₹{low:,.2f}")
    
    with col4:
        avg_vol = df['volume'].mean()
        st.metric("Avg Volume", f"{avg_vol:,.0f}")
    
    st.markdown("---")