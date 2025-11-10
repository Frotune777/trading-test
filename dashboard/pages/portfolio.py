"""
Portfolio page - Holdings and performance
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def portfolio_page():
    """Portfolio management"""
    st.markdown("## 💰 Portfolio Management")
    
    # Portfolio summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Value", "₹15,45,000", "+5.2%")
    with col2:
        st.metric("Invested", "₹12,00,000", "")
    with col3:
        st.metric("P&L", "₹3,45,000", "+28.75%")
    with col4:
        st.metric("Day Change", "₹12,500", "+0.81%")
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    # Holdings table
    st.markdown('<p class="section-header">📊 Holdings</p>', unsafe_allow_html=True)
    
    holdings_data = pd.DataFrame({
        'Symbol': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK'],
        'Quantity': [50, 100, 150, 75],
        'Avg Price': ['₹2,400', '₹3,200', '₹1,450', '₹1,600'],
        'LTP': ['₹2,450', '₹3,525', '₹1,520', '₹1,650'],
        'P&L %': ['+2.08%', '+10.16%', '+4.83%', '+3.13%']
    })
    
    st.dataframe(holdings_data, width='stretch', hide_index=True)