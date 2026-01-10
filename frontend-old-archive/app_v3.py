# dashboard/app_v3.py
"""
Fortune Trading Dashboard v3.6 - With Database Explorer
Main application entry point with all features
Author: Fortune Trading Team
Version: 3.6 - Complete with Models, Validation, MTF Analysis & Database Explorer
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import configuration
from dashboard.config import PAGE_CONFIG
from dashboard.styles.theme import DARK_THEME_CSS
from dashboard.components.navigation import render_navigation

# ============================================================================
# IMPORT ALL PAGES WITH ERROR HANDLING
# ============================================================================

# Analytics Page
try:
    from dashboard.pages.analytics import analytics_page
except ImportError as e:
    st.error(f"❌ Error importing analytics: {e}")
    analytics_page = None

# Trading Page
try:
    from dashboard.pages.trading import trading_page
except ImportError as e:
    st.error(f"❌ Error importing trading: {e}")
    trading_page = None

# Portfolio Page
try:
    from dashboard.pages.portfolio import portfolio_page
except ImportError as e:
    st.error(f"❌ Error importing portfolio: {e}")
    portfolio_page = None

# Data Manager Page
try:
    from dashboard.pages.data_manager import data_manager_page
except ImportError as e:
    st.error(f"❌ Error importing data_manager: {e}")
    data_manager_page = None

# Database Explorer Page (NEW)
try:
    from dashboard.pages.database_explorer import database_explorer_page
except ImportError as e:
    st.error(f"❌ Error importing database explorer: {e}")
    database_explorer_page = None

# Models Page
try:
    from dashboard.pages.models import models_page
except ImportError as e:
    st.error(f"❌ Error importing models: {e}")
    models_page = None

# MTF Analysis Page
try:
    from dashboard.pages.mtf_analysis import mtf_analysis_page
except ImportError as e:
    st.error(f"❌ Error importing MTF analysis: {e}")
    mtf_analysis_page = None

# Research Page
try:
    from dashboard.pages.research import research_page
except ImportError as e:
    st.error(f"❌ Error importing research: {e}")
    research_page = None

# Settings Page
try:
    from dashboard.pages.settings import settings_page
except ImportError as e:
    st.error(f"❌ Error importing settings: {e}")
    settings_page = None


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(**PAGE_CONFIG)

# Apply dark theme CSS
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    
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


initialize_session_state()


# ============================================================================
# PLACEHOLDER PAGES (Fallback if imports fail)
# ============================================================================

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
        "Database Explorer": database_explorer_page is not None,
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


# ============================================================================
# SYSTEM STATUS INDICATOR
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
            database_explorer_page is not None,  # Added
            models_page is not None,
            mtf_analysis_page is not None,
            research_page is not None,
            settings_page is not None,
        ])
        
        total_pages = 9  # Updated from 8 to 9
        
        # Status metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Pages", f"{loaded_pages}/{total_pages}")
        with col2:
            health = "🟢" if loaded_pages == total_pages else "🟡" if loaded_pages > 6 else "🔴"
            st.metric("Health", health)
        
        # Last refresh
        if st.session_state.last_data_refresh:
            refresh_time = st.session_state.last_data_refresh.strftime("%H:%M:%S")
            st.caption(f"Last refresh: {refresh_time}")
        else:
            st.caption("No data loaded")
        
        # Quick refresh button
        if st.button("🔄 Refresh Data", width='stretch'):
            st.session_state.last_data_refresh = datetime.now()
            st.success("Data refreshed!")
            st.rerun()


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    
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
            'Database': database_explorer_page or (lambda: placeholder_page('Database Explorer')),  # NEW
            'Models': models_page or (lambda: placeholder_page('Models')),
            'MTF': mtf_analysis_page or (lambda: placeholder_page('MTF Analysis')),
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


def render_footer():
    """Render application footer"""
    st.markdown('<hr>', unsafe_allow_html=True)
    
    footer_cols = st.columns([2, 1, 1])
    
    with footer_cols[0]:
        st.markdown(
            f'<div class="muted">'
            f'💡 <strong>Fortune Trading Dashboard v3.6</strong> | '
            f'Last refresh: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
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
            database_explorer_page is not None,  # Added
            models_page is not None,
            mtf_analysis_page is not None,
            research_page is not None,
            settings_page is not None,
        ])
        st.markdown(
            f'<div class="muted" style="text-align: center;">'
            f'📄 {active_pages}/9 pages active'
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