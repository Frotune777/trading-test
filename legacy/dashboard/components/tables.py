"""
Table display components
"""

import streamlit as st
import pandas as pd
from dashboard.utils.formatters import safe_get_dict_value, safe_format_currency


def render_period_summary(snapshot: dict, last_update):
    """Render period summary table"""
    st.markdown('<p class="section-header">📅 Period Summary</p>', unsafe_allow_html=True)
    
    summary_data = {
        'Metric': [
            'Last Update',
            'Market Cap',
            'P/E Ratio',
            'Book Value',
            '52W High',
            '52W Low'
        ],
        'Value': [
            last_update.strftime('%Y-%m-%d %H:%M') if last_update else 'Never',
            safe_get_dict_value(snapshot, 'market_cap', 'N/A', lambda x: str(x)),
            safe_get_dict_value(snapshot, 'pe_ratio', 'N/A', lambda x: f"{float(x):.2f}"),
            safe_get_dict_value(snapshot, 'book_value', 'N/A', lambda x: safe_format_currency(x)),
            safe_get_dict_value(snapshot, 'high_52w', 'N/A', lambda x: safe_format_currency(x)),
            safe_get_dict_value(snapshot, 'low_52w', 'N/A', lambda x: safe_format_currency(x))
        ]
    }
    
    df = pd.DataFrame(summary_data)
    st.dataframe(df, width='stretch', hide_index=True)


def render_quarterly_results(quarterly: pd.DataFrame):
    """Render quarterly results table"""
    st.markdown('<p class="section-header">📊 Quarterly Performance</p>', unsafe_allow_html=True)
    
    if quarterly is None or quarterly.empty:
        st.info("📊 No quarterly data available. Click 'Update' to fetch latest data.")
        return
    
    try:
        recent_q = quarterly.head(4)
        
        metrics_data = {
            'Quarter': [str(q) for q in recent_q['quarter'].tolist()],
            'Sales (Cr)': [safe_format_currency(x, 0) for x in recent_q['sales']],
            'Profit (Cr)': [safe_format_currency(x, 0) for x in recent_q['net_profit']],
            'EPS': [safe_format_currency(x, 2) for x in recent_q['eps']]
        }
        
        df = pd.DataFrame(metrics_data)
        st.dataframe(df, width='stretch', hide_index=True)
    except Exception as e:
        st.warning(f"⚠️ Error displaying quarterly data: {e}")


def render_peer_comparison(peers: pd.DataFrame):
    """Render peer comparison table"""
    st.markdown('<p class="section-header">🏢 Peer Comparison</p>', unsafe_allow_html=True)
    
    if peers is None or peers.empty:
        st.info("🏢 No peer data available")
        return
    
    try:
        peers_display = peers[['peer_name', 'cmp', 'pe', 'market_cap']].head(5)
        st.dataframe(peers_display, width='stretch', hide_index=True)
    except Exception as e:
        st.info("🏢 No peer data available")