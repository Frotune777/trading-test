"""
Chart rendering components
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from frontend.config import CHART_COLORS


def render_price_chart(price_history: pd.DataFrame, symbol: str):
    """Render price and volume charts"""
    st.markdown('<p class="section-header">📈 Price Performance</p>', unsafe_allow_html=True)
    
    if price_history is None or price_history.empty or len(price_history) < 2:
        st.warning("📉 No price history available. Click 'Update' to fetch data.")
        return
    
    try:
        price_history = price_history.copy()
        
        # Calculate returns
        first_close = price_history['close'].iloc[0]
        if first_close > 0:
            price_history['returns'] = ((price_history['close'] / first_close) - 1) * 100
        else:
            price_history['returns'] = 0
        
        # Price chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=price_history['date'],
            y=price_history['returns'],
            name='Cumulative Return',
            fill='tozeroy',
            line=dict(color='#4a90e2', width=2),
            fillcolor='rgba(74, 144, 226, 0.3)',
            hovertemplate='<b>Date</b>: %{x}<br><b>Return</b>: %{y:.2f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(text=f'{symbol} - Cumulative Return (1 Year)', font=dict(color='#e6edf3')),
            xaxis=dict(title='Date', gridcolor='#2d3748', color='#e6edf3'),
            yaxis=dict(title='Cumulative Return (%)', gridcolor='#2d3748', color='#e6edf3'),
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified',
            height=500,
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(color='#e6edf3')
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Volume chart
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(
            x=price_history['date'],
            y=price_history['volume'],
            name='Volume',
            marker_color='#4a90e2',
            opacity=0.6,
            hovertemplate='<b>Date</b>: %{x}<br><b>Volume</b>: %{y:,.0f}<extra></extra>'
        ))
        
        fig_vol.update_layout(
            title=dict(text='Trading Volume', font=dict(color='#e6edf3')),
            xaxis=dict(gridcolor='#2d3748', color='#e6edf3'),
            yaxis=dict(gridcolor='#2d3748', color='#e6edf3'),
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=200,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
            font=dict(color='#e6edf3')
        )
        
        st.plotly_chart(fig_vol, width='stretch')
        
    except Exception as e:
        st.error(f"❌ Error rendering chart: {e}")


def render_shareholding_chart(shareholding: pd.DataFrame):
    """Render shareholding pie chart"""
    st.markdown('<p class="section-header">👥 Shareholding Pattern</p>', unsafe_allow_html=True)
    
    if shareholding is None or shareholding.empty:
        st.info("👥 No shareholding data available.")
        return
    
    try:
        latest = shareholding.iloc[0]
        labels, values = [], []
        
        for holder in ['promoters', 'fii', 'dii', 'public', 'government']:
            val = latest.get(holder)
            if val and pd.notna(val) and val > 0:
                labels.append(holder.upper())
                values.append(float(val))
        
        if values:
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.5,
                marker_colors=CHART_COLORS[:len(labels)],
                textinfo='label+percent',
                textfont=dict(color='white', size=14),
                hovertemplate='<b>%{label}</b><br>%{value:.2f}%<extra></extra>'
            )])
            
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=True,
                legend=dict(orientation='h', yanchor='bottom', y=-0.2, font=dict(color='#e6edf3')),
                font=dict(color='#e6edf3')
            )
            
            st.plotly_chart(fig, width='stretch')
    except Exception as e:
        st.warning(f"⚠️ Error displaying shareholding: {e}")