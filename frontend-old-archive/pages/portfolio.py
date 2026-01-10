"""
Portfolio page - Holdings and performance
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def portfolio_page():
    """Portfolio management"""
    from frontend.utils.data_loader import get_database
    
    st.markdown("## 💰 Portfolio Management")
    
    db = get_database()
    
    # --- Add New Position Section ---
    with st.expander("➕ Add / Update Position"):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            # Get list of companies for dropdown
            companies = db.get_all_companies()
            symbols = sorted([c['symbol'] for c in companies]) if companies else []
            symbol_input = st.selectbox("Symbol", symbols) if symbols else st.text_input("Symbol (Add stocks in Data Manager first)")
        
        with col2:
            qty_input = st.number_input("Quantity", min_value=1, value=10)
        
        with col3:
            price_input = st.number_input("Avg Price", min_value=0.0, value=0.0, step=0.05)
            
        with col4:
            st.write("") # Spacer
            st.write("") 
            if st.button("Save Position", type="primary", use_container_width=True):
                if symbol_input and qty_input > 0:
                    try:
                        db.add_portfolio_holding(symbol_input, qty_input, price_input)
                        st.success(f"Saved {symbol_input}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Invalid input")

    st.markdown('<hr>', unsafe_allow_html=True)

    # --- Fetch Holdings ---
    try:
        holdings = db.get_portfolio_holdings()
    except Exception:
        # DB schema might need update if table missing
        st.error("Portfolio table missing. Please restart the app to initialize the database schema.")
        return

    if not holdings:
        st.info("Your portfolio is empty. Add positions above.")
        return

    # --- Calculate Portfolio Metrics ---
    portfolio_data = []
    
    total_invested = 0.0
    total_current_value = 0.0
    
    for h in holdings:
        symbol = h['symbol']
        qty = h['quantity']
        avg_price = h['avg_price']
        
        # Get live price
        snapshot = db.get_snapshot(symbol)
        ltp = snapshot['current_price'] if snapshot and snapshot.get('current_price') else avg_price
        
        invested = qty * avg_price
        current_value = qty * ltp
        pnl = current_value - invested
        pnl_percent = (pnl / invested * 100) if invested > 0 else 0
        
        total_invested += invested
        total_current_value += current_value
        
        portfolio_data.append({
            'Symbol': symbol,
            'Company': h.get('company_name', symbol),
            'Quantity': qty,
            'Avg Price': avg_price,
            'LTP': ltp,
            'Invested': invested,
            'Current Value': current_value,
            'P&L': pnl,
            'P&L %': pnl_percent
        })
    
    total_pnl = total_current_value - total_invested
    total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    # --- Summary Metrics ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Value", f"₹{total_current_value:,.0f}")
    with col2:
        st.metric("Invested", f"₹{total_invested:,.0f}")
    with col3:
        st.metric("Total P&L", f"₹{total_pnl:,.0f}", f"{total_pnl_percent:+.2f}%")
    with col4:
        # Simple Day Change approximation (requires prev close which we check)
        # Using simple assumption for demo 
        st.metric("Positions", len(holdings))

    st.markdown('<hr>', unsafe_allow_html=True)
    
    # --- Holdings Table ---
    st.markdown('<p class="section-header">📊 Holdings</p>', unsafe_allow_html=True)
    
    df = pd.DataFrame(portfolio_data)
    
    # Format for display
    display_df = df.copy()
    display_df['Avg Price'] = display_df['Avg Price'].apply(lambda x: f"₹{x:,.2f}")
    display_df['LTP'] = display_df['LTP'].apply(lambda x: f"₹{x:,.2f}")
    display_df['Invested'] = display_df['Invested'].apply(lambda x: f"₹{x:,.0f}")
    display_df['Current Value'] = display_df['Current Value'].apply(lambda x: f"₹{x:,.0f}")
    display_df['P&L'] = display_df['P&L'].apply(lambda x: f"₹{x:,.0f}")
    display_df['P&L %'] = display_df['P&L %'].apply(lambda x: f"{x:+.2f}%")
    
    st.dataframe(
        display_df[['Symbol', 'Company', 'Quantity', 'Avg Price', 'LTP', 'Invested', 'Current Value', 'P&L', 'P&L %']], 
        width='stretch', 
        hide_index=True
    )
    
    # --- Remove Position ---
    with st.expander("🗑️ Remove Position"):
        to_remove = st.selectbox("Select symbol to remove", [h['Symbol'] for h in portfolio_data])
        if st.button("Remove Selected"):
            db.remove_portfolio_holding(to_remove)
            st.success(f"Removed {to_remove}")
            st.rerun()

if __name__ == "__main__":
    portfolio_page()