"""
Fortune Trading Dashboard v3.5 - Production Ready with MTF Analysis
Main application entry point with all features
Author: Fortune Trading Team
Version: 3.5 - Complete with Models, Validation & MTF Analysis
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
import time # Added for data fetching delay

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import configuration
from dashboard.config import PAGE_CONFIG
from dashboard.styles.theme import DARK_THEME_CSS
from dashboard.components.navigation import render_navigation

# IMPORTANT: You must create this file and function!
# It should contain the logic to query your database for the table counts.
try:
    from utils.data_status import fetch_table_statistics
    DATA_STATUS_MODULE_LOADED = True
except ImportError as e:
    # Fallback if the utility file hasn't been created yet
    st.error(f"❌ CRITICAL: Missing utility to fetch table stats: {e}")
    st.info("Please ensure 'utils/data_status.py' and 'fetch_table_statistics' function exist.")
    DATA_STATUS_MODULE_LOADED = False


# ============================================================================
# IMPORT ALL PAGES WITH ERROR HANDLING (UNCHANGED)
# ============================================================================

# Analytics Page
try:
    from dashboard.pages.analytics import analytics_page
except ImportError as e:
    # st.error(f"❌ Error importing analytics: {e}") # Suppress error here to avoid clutter
    analytics_page = None

# Trading Page
try:
    from dashboard.pages.trading import trading_page
except ImportError as e:
    trading_page = None

# Portfolio Page
try:
    from dashboard.pages.portfolio import portfolio_page
except ImportError as e:
    portfolio_page = None

# Data Manager Page
try:
    from dashboard.pages.data_manager import data_manager_page
except ImportError as e:
    data_manager_page = None

# Models Page
try:
    from dashboard.pages.models import models_page
except ImportError as e:
    models_page = None

# MTF Analysis Page (NEW)
try:
    from dashboard.pages.mtf_analysis import mtf_analysis_page
except ImportError as e:
    mtf_analysis_page = None

# Research Page
try:
    from dashboard.pages.research import research_page
except ImportError as e:
    research_page = None

# Settings Page
try:
    from dashboard.pages.settings import settings_page
except ImportError as e:
    settings_page = None


# ============================================================================
# PAGE CONFIGURATION (UNCHANGED)
# ============================================================================

st.set_page_config(**PAGE_CONFIG)
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)


# ============================================================================
# DATA FETCHING AND CACHING LOGIC (NEW SECTION)
# ============================================================================

# The cache ensures we don't hit the DB on every single Streamlit rerun
@st.cache_data(ttl=600) # Cache for 10 minutes
def get_dashboard_statistics():
    """Fetches table statistics from the database."""
    if DATA_STATUS_MODULE_LOADED:
        try:
            # THIS IS THE KEY CALL TO YOUR EXTERNAL DB LOGIC
            stats = fetch_table_statistics()
            # Simulate a small delay to prevent rapid execution
            time.sleep(0.5) 
            return stats
        except Exception as e:
            st.error(f"DB Error: Failed to fetch table statistics: {e}")
            return None
    return None # Return None if module failed to load

# ============================================================================
# SESSION STATE INITIALIZATION (REVISED)
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables and fetch initial data."""
    
    # Active page
    if 'active_page' not in st.session_state:
        st.session_state.active_page = 'Analytics'
    
    # Selected symbol
    if 'selected_symbol' not in st.session_state:
        st.session_state.selected_symbol = None
    
    # Validation results
    if 'validation_results' not in st.session_state:
        st.session_state.validation_results = {}
    
    # MTF analysis state
    if 'mtf_timeframes' not in st.session_state:
        st.session_state.mtf_timeframes = ['1D', '1W', '1M']
    
    # Cache timestamps
    if 'last_data_refresh' not in st.session_state:
        st.session_state.last_data_refresh = None
    
    # User preferences
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True
    
    # Alert settings
    if 'alerts_enabled' not in st.session_state:
        st.session_state.alerts_enabled = True
        
    # **REVISED: Table Statistics Cache**
    if 'table_statistics' not in st.session_state:
        st.session_state.table_statistics = get_dashboard_statistics() # Initial fetch
        if st.session_state.table_statistics:
             st.session_state.last_data_refresh = datetime.now()


initialize_session_state()


# ============================================================================
# SYSTEM STATUS INDICATOR (REVISED)
# ============================================================================

def render_system_status():
    """Render system status indicators in sidebar"""
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📊 System Status")
        
        # Count loaded pages
        loaded_pages = sum([
            analytics_page is not None,
            trading_page is not None,
            portfolio_page is not None,
            data_manager_page is not None,
            models_page is not None,
            mtf_analysis_page is not None,
            research_page is not None,
            settings_page is not None,
        ])
        
        total_pages = 8
        
        # Status metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Pages", f"{loaded_pages}/{total_pages}")
        with col2:
            # Check for empty tables dynamically
            stats = st.session_state.table_statistics
            if stats is not None:
                # Assuming the stats is a list of tuples: (table_name, count, status, quality)
                # Count tables with 0 records
                empty_tables = sum(1 for _, count, _, _ in stats if count == 0)
                if empty_tables == 0:
                    health = "🟢"
                elif empty_tables < 5:
                    health = "🟡"
                else:
                    health = "🔴"
                st.metric("Health", health, delta=f"-{empty_tables} Empty")
            else:
                 st.metric("Health", "⚫️ DB Down")
        
        # Last refresh
        if st.session_state.last_data_refresh:
            refresh_time = st.session_state.last_data_refresh.strftime("%H:%M:%S")
            st.caption(f"Last data count: {refresh_time}")
        else:
            st.caption("No data loaded")
        
        # Quick refresh button - NOW REFRESHES STATS CACHE
        if st.button("🔄 Refresh Data Counts", width='stretch'):
            # Clear the cache for the stats function
            get_dashboard_statistics.clear() 
            st.session_state.table_statistics = get_dashboard_statistics()
            st.session_state.last_data_refresh = datetime.now()
            st.success("Data counts refreshed!")
            st.rerun()


# ============================================================================
# MAIN APPLICATION (UNCHANGED)
# ============================================================================

def main():
    """Main application entry point"""
    
    # ... [Rest of the main function remains the same] ...
    
    try:
        # Render navigation
        render_navigation()
        
        # Render system status in sidebar
        render_system_status()
        
        # Add spacing after navigation
        st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
        
        # Page routing with fallbacks
        page_map = {
            'Analytics': analytics_page or (lambda: placeholder_page('Analytics')),
            'Trading': trading_page or (lambda: placeholder_page('Trading')),
            'Portfolio': portfolio_page or (lambda: placeholder_page('Portfolio')),
            'Data': data_manager_page or (lambda: placeholder_page('Data Manager')),
            'Models': models_page or (lambda: placeholder_page('Models')),
            'MTF': mtf_analysis_page or (lambda: placeholder_page('MTF Analysis')),  # NEW
            'Research': research_page or (lambda: placeholder_page('Research')),
            'Settings': settings_page or (lambda: placeholder_page('Settings')),
        }
        
        # Get current page
        current_page = st.session_state.active_page
        
        # Execute page function
        page_function = page_map.get(current_page)
        
        if page_function:
            try:
                # Page container with error boundary
                with st.container():
                    page_function()
                    
            except Exception as e:
                st.error(f"❌ Error loading {current_page} page")
                
                with st.expander("🐛 Error Details", expanded=True):
                    st.exception(e)
                
                st.warning("""
                **Recovery Options:**
                - 🔄 Refresh the page (Ctrl+R or Cmd+R)
                - 🏠 Return to Analytics page
                - ⚙️ Check Settings for configuration issues
                - 📥 Visit Data page to verify data availability
                """)
                
                # Quick recovery buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔄 Refresh"):
                        st.rerun()
                with col2:
                    if st.button("🏠 Analytics"):
                        st.session_state.active_page = 'Analytics'
                        st.rerun()
                with col3:
                    if st.button("⚙️ Settings"):
                        st.session_state.active_page = 'Settings'
                        st.rerun()
        else:
            st.error(f"❌ Page '{current_page}' not found")
            st.info("**Available pages:** " + ", ".join(page_map.keys()))
            
            if st.button("🏠 Return to Analytics"):
                st.session_state.active_page = 'Analytics'
                st.rerun()
        
        # Footer
        render_footer()
    
    except Exception as e:
        st.error(f"💥 Critical application error")
        
        with st.expander("🔍 Error Details", expanded=True):
            st.exception(e)
        
        # Emergency recovery
        st.markdown("---")
        st.warning("""
        ### 🚨 Emergency Recovery Options:
        
        1. **Refresh Page**: Press `Ctrl+R` (Windows) or `Cmd+R` (Mac)
        2. **Clear Cache**: Run `streamlit cache clear` in terminal
        3. **Restart App**: Stop (Ctrl+C) and restart `streamlit run dashboard/app_v3.py`
        4. **Check Logs**: Review terminal output for detailed errors
        5. **Verify Setup**: Ensure all dependencies are installed
        
        **Need Help?**
        - Check `README.md` for setup instructions
        - Review `requirements.txt` for dependencies
        - Verify database connectivity in Settings
        """)
        
        # Emergency navigation
        st.markdown("### 🆘 Emergency Navigation")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Force Refresh"):
                st.session_state.clear()
                st.rerun()
        with col2:
            if st.button("🏠 Reset to Home"):
                st.session_state.active_page = 'Analytics'
                st.rerun()
        with col3:
            if st.button("⚙️ Open Settings"):
                st.session_state.active_page = 'Settings'
                st.rerun()


def placeholder_page(page_name: str):
    """Placeholder page when actual page fails to load"""
    st.markdown(f"## 🚧 {page_name}")
    
    st.error(f"❌ Error loading {page_name} page")
    
    st.info(f"""
    **Troubleshooting Steps:**
    1. Check if `dashboard/pages/{page_name.lower().replace(' ', '_')}.py` exists
    2. Verify all imports in the file are correct
    3. Check for syntax errors in the page file
    4. Ensure all dependencies are installed
    5. Restart the Streamlit application
    """)
    
    # Show import error details
    st.markdown("### 🔍 Import Status")
    
    import_status = {
        "Analytics": analytics_page is not None,
        "Trading": trading_page is not None,
        "Portfolio": portfolio_page is not None,
        "Data Manager": data_manager_page is not None,
        "Models": models_page is not None,
        "MTF Analysis": mtf_analysis_page is not None,
        "Research": research_page is not None,
        "Settings": settings_page is not None,
    }
    
    cols = st.columns(4)
    for idx, (page, status) in enumerate(import_status.items()):
        with cols[idx % 4]:
            icon = "✅" if status else "❌"
            st.metric(page, icon)
    
    # Quick actions
    st.markdown("### 🛠️ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reload Page"):
            st.rerun()
    
    with col2:
        if st.button("🏠 Go to Analytics"):
            st.session_state.active_page = 'Analytics'
            st.rerun()
    
    with col3:
        if st.button("⚙️ Open Settings"):
            st.session_state.active_page = 'Settings'
            st.rerun()


def render_footer():
    """Render application footer"""
    st.markdown('<hr>', unsafe_allow_html=True)
    
    footer_cols = st.columns([2, 1, 1])
    
    with footer_cols[0]:
        st.markdown(
            f'<div class="muted">'
            f'💡 <strong>Fortune Trading Dashboard v3.5</strong> | '
            f'Last check: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            f'</div>',
            unsafe_allow_html=True
        )
    
    with footer_cols[1]:
        # Page count indicator
        active_pages = sum([
            analytics_page is not None,
            trading_page is not None,
            portfolio_page is not None,
            data_manager_page is not None,
            models_page is not None,
            mtf_analysis_page is not None,
            research_page is not None,
            settings_page is not None,
        ])
        st.markdown(
            f'<div class="muted" style="text-align: center;">'
            f'📄 {active_pages}/8 pages active'
            f'</div>',
            unsafe_allow_html=True
        )
    
    with footer_cols[2]:
        # Current page indicator
        st.markdown(
            f'<div class="muted" style="text-align: right;">'
            f'📍 {st.session_state.active_page}'
            f'</div>',
            unsafe_allow_html=True
        )


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        st.info("👋 Application stopped by user")
    except Exception as e:
        st.error(f"💥 Fatal error: {e}")
        st.exception(e)