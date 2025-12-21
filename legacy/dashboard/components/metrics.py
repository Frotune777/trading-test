"""
Metric display components
"""

import streamlit as st
import pandas as pd
from dashboard.utils.formatters import safe_num


def render_metrics_row(metrics: dict):
    """Render key metrics in a row"""
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        current_price = safe_num(metrics.get('current_price', 0))
        change_percent = safe_num(metrics.get('change_percent', 0))
        
        st.metric(
            "Current Price",
            f"₹{current_price:,.2f}",
            f"{change_percent:+.2f}%" if change_percent != 0 else None
        )
    
    with col2:
        total_return = safe_num(metrics.get('total_return', 0))
        st.metric("Total Return (1Y)", f"{total_return:+.2f}%")
    
    with col3:
        volatility = safe_num(metrics.get('volatility', 0))
        st.metric("Volatility", f"{volatility:.2f}%")
    
    with col4:
        max_drawdown = safe_num(metrics.get('max_drawdown', 0))
        st.metric("Max Drawdown", f"{max_drawdown:.2f}%")
    
    with col5:
        sharpe_ratio = safe_num(metrics.get('sharpe_ratio', 0))
        st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
    
    with col6:
        avg_volume = safe_num(metrics.get('avg_volume', 0))
        st.metric("Avg Volume", f"{int(avg_volume):,}")