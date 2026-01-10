# dashboard/components/navigation.py
"""
Navigation components
Version: 3.5 - With Database Explorer
"""

import streamlit as st


def render_navigation():
    """Render top navigation bar"""
    
    # Define pages with icons
    PAGES = {
        '📈 Analytics': 'Analytics',
        '💹 Trading': 'Trading',
        '💼 Portfolio': 'Portfolio',
        '📥 Data': 'Data',
        '🗄️ Database': 'Database',  # NEW
        '🤖 Models': 'Models',
        '📊 MTF': 'MTF',
        '🔬 Research': 'Research',
        '⚙️ Settings': 'Settings'
    }
    
    # Custom CSS for navigation
    st.markdown("""
        <style>
            .nav-container {
                position: relative;
                z-index: 100 !important;
                margin-bottom: 1rem;
            }
            /* Smaller buttons for more items */
            .stButton > button {
                font-size: 0.9rem !important;
                padding: 0.4rem 0.6rem !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    
    # Create columns for navigation buttons
    cols = st.columns(len(PAGES))
    
    for i, (display_name, page_name) in enumerate(PAGES.items()):
        with cols[i]:
            # Determine button type based on active page
            button_type = "primary" if st.session_state.active_page == page_name else "secondary"
            
            # Create navigation button
            if st.button(
                display_name,
                key=f"nav_{page_name}",
                width='stretch',  # Fixed deprecation warning
                type=button_type
            ):
                st.session_state.active_page = page_name
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)