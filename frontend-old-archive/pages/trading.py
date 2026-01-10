"""
Trading page - Order placement and positions
"""

import streamlit as st
import pandas as pd


def trading_page():
    """Trading interface"""
    st.markdown("## 📈 Trading Dashboard")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<p class="section-header">📊 Live Market Data</p>', unsafe_allow_html=True)
        
        symbol = st.selectbox("Select Symbol", ["RELIANCE", "TCS", "INFY", "HDFCBANK"])
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("LTP", "₹2,450.50", "+12.50 (+0.51%)")
        with col_b:
            st.metric("Volume", "12.5M", "+15%")
        with col_c:
            st.metric("Open Interest", "45.2K", "-2%")
        
        st.markdown('<hr>', unsafe_allow_html=True)
        
        # Order placement
        st.markdown('<p class="section-header">📝 Place Order</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            order_type = st.selectbox("Order Type", ["Market", "Limit", "Stop Loss"])
        with col2:
            quantity = st.number_input("Quantity", min_value=1, value=1)
        with col3:
            if order_type != "Market":
                price = st.number_input("Price", min_value=0.0, value=2450.50)
        
        col_buy, col_sell = st.columns(2)
        with col_buy:
            if st.button("🟢 BUY", width='stretch'):
                st.success(f"✅ Buy order placed for {quantity} shares")
        with col_sell:
            if st.button("🔴 SELL", width='stretch'):
                st.error(f"✅ Sell order placed for {quantity} shares")
    
    with col2:
        st.markdown('<p class="section-header">📋 Order Book</p>', unsafe_allow_html=True)
        
        orders_data = pd.DataFrame({
            'Time': ['14:30', '14:25', '14:20'],
            'Type': ['BUY', 'SELL', 'BUY'],
            'Qty': [10, 5, 15],
            'Price': ['₹2,450', '₹2,455', '₹2,448'],
            'Status': ['✅ Filled', '⏳ Pending', '✅ Filled']
        })
        st.dataframe(orders_data, width='stretch', hide_index=True)

if __name__ == "__main__":
    trading_page()