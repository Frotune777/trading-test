# dashboard/pages/analytics.py
"""
Analytics Page - Stock Analysis Dashboard
Now includes price trend visualization
Version: 3.3 - With Price Trends
"""

import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from dashboard.utils.data_loader import get_database, get_updater, load_stock_data, calculate_metrics
from dashboard.components.metrics import render_metrics_row
from dashboard.components.tables import render_period_summary, render_quarterly_results, render_peer_comparison
from dashboard.components.charts import render_shareholding_chart


def analytics_page():
    """Main analytics dashboard with price trends"""
    
    st.markdown("## 📊 Stock Analytics Dashboard")
    
    db = get_database()
    updater = get_updater()
    
    # Control panel
    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
    
    with col1:
        companies = db.get_all_companies()
        if not companies:
            st.error("❌ No stocks in database. Please add stocks first.")
            st.info("💡 Go to **Data Manager → Add New Stock** to get started!")
            st.stop()
        
        symbols = sorted([c['symbol'] for c in companies])
        default_index = 0
        if st.session_state.selected_symbol and st.session_state.selected_symbol in symbols:
            default_index = symbols.index(st.session_state.selected_symbol)
        
        selected_symbol = st.selectbox(
            '🔍 Select Stock',
            symbols,
            index=default_index
        )
        st.session_state.selected_symbol = selected_symbol
    
    with col2:
        sectors = ['All'] + sorted(list(set([c.get('sector', 'Unknown') for c in companies if c.get('sector')])))
        selected_sector = st.selectbox('🏢 Sector', sectors)
    
    with col3:
        if st.button('🔄 Refresh', width='stretch'):
            st.cache_data.clear()
            st.rerun()
    
    with col4:
        if st.button('⬇️ Update', width='stretch'):
            with st.spinner(f'Updating {selected_symbol}...'):
                try:
                    result = updater.update_stock(selected_symbol, force=True)
                    if result.get('success'):
                        st.success('✅ Updated!')
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {result.get('error', 'Update failed')}")
                except Exception as e:
                    st.error(f"❌ Update error: {str(e)}")
    
    # Status indicator
    last_update = db.get_last_update(selected_symbol)
    if last_update:
        age = datetime.now() - last_update
        hours = age.total_seconds() / 3600
        if hours < 24:
            st.markdown(f'<div class="status-online">● Online - Last updated {int(hours)}h ago</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-offline">● Stale data - {int(hours/24)}d old</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-offline">● No data - Click Update</div>', unsafe_allow_html=True)
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    # Load data
    with st.spinner(f'Loading {selected_symbol}...'):
        data = load_stock_data(selected_symbol)
    
    if not data:
        st.error("❌ Failed to load stock data")
        st.info("💡 Click the 'Update' button to fetch data from NSE")
        st.stop()
    
    # Calculate and render metrics
    try:
        metrics = calculate_metrics(data['price_history'], data['snapshot'])
        render_metrics_row(metrics)
    except Exception as e:
        st.error(f"Error displaying metrics: {e}")
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    # Two-column layout
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            render_period_summary(data['snapshot'], data['last_update'])
        except Exception as e:
            st.warning(f"⚠️ Error: {e}")
    
    with col2:
        try:
            render_quarterly_results(data['quarterly'])
        except Exception as e:
            st.warning(f"⚠️ Error: {e}")
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    # ========================================================================
    # PRICE TREND CHART (NEW FEATURE)
    # ========================================================================
    
    render_price_trend_chart(data['price_history'], selected_symbol)
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    # Shareholding and Peers
    col1, col2 = st.columns([1, 1])
    
    with col1:
        try:
            render_shareholding_chart(data['shareholding'])
        except Exception as e:
            st.warning(f"⚠️ Error: {e}")
    
    with col2:
        try:
            render_peer_comparison(data['peers'])
        except Exception as e:
            st.warning(f"⚠️ Error: {e}")


# ============================================================================
# PRICE TREND CHART (NEW)
# ============================================================================

def render_price_trend_chart(price_history: pd.DataFrame, symbol: str):
    """
    Render comprehensive price trend analysis
    Shows: Price movement, Volume, Moving averages
    """
    st.markdown('<p class="section-header">📈 Price Trend Analysis</p>', unsafe_allow_html=True)
    
    if price_history is None or price_history.empty or len(price_history) < 2:
        st.warning("📉 No price history available. Click 'Update' to fetch data.")
        st.info("💡 Price trend shows historical price movements and volume patterns")
        return
    
    try:
        # Prepare data
        df = price_history.copy()
        df = df.sort_values('date')
        
        # Calculate moving averages
        if len(df) >= 20:
            df['MA20'] = df['close'].rolling(window=20).mean()
        if len(df) >= 50:
            df['MA50'] = df['close'].rolling(window=50).mean()
        if len(df) >= 200:
            df['MA200'] = df['close'].rolling(window=200).mean()
        
        # Time period selector
        col1, col2, col3, col4, col5 = st.columns(5)
        
        period_options = {
            '1M': 30,
            '3M': 90,
            '6M': 180,
            '1Y': 365,
            'All': len(df)
        }
        
        selected_period = col1.selectbox("Period", list(period_options.keys()), index=3)
        days = period_options[selected_period]
        
        # Filter data by period
        df_display = df.tail(min(days, len(df)))
        
        # Create candlestick chart
        fig = go.Figure()
        
        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df_display['date'],
            open=df_display['open'],
            high=df_display['high'],
            low=df_display['low'],
            close=df_display['close'],
            name='OHLC',
            increasing_line_color='#2ecc71',
            decreasing_line_color='#e74c3c'
        ))
        
        # Moving averages
        if 'MA20' in df_display.columns and df_display['MA20'].notna().any():
            fig.add_trace(go.Scatter(
                x=df_display['date'],
                y=df_display['MA20'],
                name='MA20',
                line=dict(color='#4a90e2', width=1.5),
                opacity=0.7
            ))
        
        if 'MA50' in df_display.columns and df_display['MA50'].notna().any():
            fig.add_trace(go.Scatter(
                x=df_display['date'],
                y=df_display['MA50'],
                name='MA50',
                line=dict(color='#f39c12', width=1.5),
                opacity=0.7
            ))
        
        if 'MA200' in df_display.columns and df_display['MA200'].notna().any():
            fig.add_trace(go.Scatter(
                x=df_display['date'],
                y=df_display['MA200'],
                name='MA200',
                line=dict(color='#9b59b6', width=1.5),
                opacity=0.7
            ))
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=f'{symbol} - Price Trend ({selected_period})',
                font=dict(color='#e6edf3', size=18)
            ),
            xaxis=dict(
                title='Date',
                gridcolor='#2d3748',
                color='#e6edf3',
                rangeslider=dict(visible=False)
            ),
            yaxis=dict(
                title='Price (₹)',
                gridcolor='#2d3748',
                color='#e6edf3'
            ),
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified',
            height=500,
            margin=dict(l=50, r=50, t=50, b=50),
            font=dict(color='#e6edf3'),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(color='#e6edf3')
            )
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Volume chart
        st.markdown("**📊 Trading Volume**")
        
        fig_vol = go.Figure()
        
        # Color code volume bars (green if price up, red if down)
        colors = ['#2ecc71' if close >= open_ else '#e74c3c' 
                  for close, open_ in zip(df_display['close'], df_display['open'])]
        
        fig_vol.add_trace(go.Bar(
            x=df_display['date'],
            y=df_display['volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.6,
            hovertemplate='<b>Date</b>: %{x}<br><b>Volume</b>: %{y:,.0f}<extra></extra>'
        ))
        
        fig_vol.update_layout(
            xaxis=dict(
                gridcolor='#2d3748',
                color='#e6edf3'
            ),
            yaxis=dict(
                title='Volume',
                gridcolor='#2d3748',
                color='#e6edf3'
            ),
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=200,
            margin=dict(l=50, r=50, t=20, b=50),
            showlegend=False,
            font=dict(color='#e6edf3')
        )
        
        st.plotly_chart(fig_vol, width='stretch')
        
        # Key insights
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            first_price = df_display['close'].iloc[0]
            last_price = df_display['close'].iloc[-1]
            change = ((last_price / first_price) - 1) * 100
            st.metric(
                f"Change ({selected_period})",
                f"{change:+.2f}%",
                f"₹{last_price - first_price:+,.2f}"
            )
        
        with col2:
            high_price = df_display['high'].max()
            st.metric(
                f"High ({selected_period})",
                f"₹{high_price:,.2f}"
            )
        
        with col3:
            low_price = df_display['low'].min()
            st.metric(
                f"Low ({selected_period})",
                f"₹{low_price:,.2f}"
            )
        
        with col4:
            avg_volume = df_display['volume'].mean()
            st.metric(
                "Avg Volume",
                f"{avg_volume:,.0f}"
            )
        
    except Exception as e:
        st.error(f"❌ Error rendering chart: {e}")
        st.info("Please try updating the data or selecting a different stock")