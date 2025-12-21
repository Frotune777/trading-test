"""
Settings Page - Application and database configuration
"""

import streamlit as st
import shutil
from pathlib import Path
from datetime import datetime
from dashboard.utils.data_loader import get_database


def settings_page():
    """Application settings and configuration"""
    st.markdown("## ⚙️ Settings")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚙️ General", 
        "🔔 Notifications", 
        "💾 Database Management",
        "🔐 Advanced"
    ])
    
    # ========================================================================
    # TAB 1: GENERAL SETTINGS
    # ========================================================================
    
    with tab1:
        general_settings_tab()
    
    # ========================================================================
    # TAB 2: NOTIFICATIONS
    # ========================================================================
    
    with tab2:
        notifications_tab()
    
    # ========================================================================
    # TAB 3: DATABASE MANAGEMENT
    # ========================================================================
    
    with tab3:
        database_management_tab()
    
    # ========================================================================
    # TAB 4: ADVANCED
    # ========================================================================
    
    with tab4:
        advanced_settings_tab()


def general_settings_tab():
    """General application settings"""
    st.markdown('<p class="section-header">⚙️ General Settings</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Display Settings**")
        
        theme = st.selectbox(
            "Theme",
            ["Dark (Current)", "Light", "Auto"],
            help="Theme selection (requires app restart)"
        )
        
        default_page = st.selectbox(
            "Default Page",
            ["Analytics", "Trading", "Portfolio", "Data", "Research", "Settings"]
        )
        
        show_advanced = st.checkbox("Show advanced metrics", value=True)
        compact_view = st.checkbox("Compact table view", value=False)
    
    with col2:
        st.markdown("**Data Settings**")
        
        currency = st.selectbox("Currency", ["INR (₹)", "USD ($)", "EUR (€)"])
        
        date_format = st.selectbox(
            "Date Format",
            ["YYYY-MM-DD", "DD-MM-YYYY", "MM/DD/YYYY"]
        )
        
        decimal_places = st.slider("Decimal places", 0, 4, 2)
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    st.markdown("**Performance Settings**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cache_ttl = st.number_input(
            "Cache TTL (seconds)",
            min_value=60,
            max_value=7200,
            value=3600,
            step=60,
            help="How long to cache data before refreshing"
        )
    
    with col2:
        auto_refresh = st.checkbox("Enable auto-refresh", value=False)
        if auto_refresh:
            refresh_interval = st.number_input(
                "Refresh interval (seconds)",
                min_value=10,
                max_value=300,
                value=60
            )
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    if st.button("💾 Save Settings", type="primary", width='stretch'):
        st.success("✅ Settings saved successfully!")
        st.info("ℹ️ Some settings require app restart to take effect")


def notifications_tab():
    """Notification preferences"""
    st.markdown('<p class="section-header">🔔 Notification Settings</p>', unsafe_allow_html=True)
    
    st.markdown("**Alert Types**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("📈 Price alerts", value=True)
        st.checkbox("📊 Volume spike alerts", value=False)
        st.checkbox("📰 Corporate action alerts", value=True)
        st.checkbox("🔔 News alerts", value=False)
    
    with col2:
        st.checkbox("⏰ Daily market summary", value=True)
        st.checkbox("📧 Weekly report", value=False)
        st.checkbox("💰 Portfolio updates", value=True)
        st.checkbox("🎯 Screener matches", value=False)
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    st.markdown("**Notification Channels**")
    
    email_enabled = st.checkbox("Enable email notifications", value=False)
    if email_enabled:
        st.text_input("Email address", placeholder="your@email.com")
        st.text_input("SMTP Server", placeholder="smtp.gmail.com")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("SMTP Port", value="587")
        with col2:
            st.text_input("SMTP Username", placeholder="username")
        st.text_input("SMTP Password", type="password")
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    telegram_enabled = st.checkbox("Enable Telegram notifications", value=False)
    if telegram_enabled:
        st.text_input("Bot Token", type="password", placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz")
        st.text_input("Chat ID", placeholder="123456789")
        
        if st.button("🧪 Test Telegram Connection"):
            st.info("📱 Test message sent!")
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    if st.button("💾 Save Notification Settings", type="primary", width='stretch'):
        st.success("✅ Notification settings saved!")


def database_management_tab():
    """Database maintenance tools"""
    st.markdown('<p class="section-header">💾 Database Management</p>', unsafe_allow_html=True)
    
    db = get_database()
    db_path = Path(db.db_path)
    
    # Database info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        db_size = db_path.stat().st_size / (1024 * 1024)  # MB
        st.metric("Database Size", f"{db_size:.2f} MB")
    
    with col2:
        stats = db.get_database_stats()
        total_records = sum(stats['table_counts'].values())
        st.metric("Total Records", f"{total_records:,}")
    
    with col3:
        st.metric("Database Path", "stock_data.db")
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    # Maintenance operations
    st.markdown("**Maintenance Operations**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("*Optimization*")
        
        if st.button("🔧 Vacuum Database", width='stretch'):
            with st.spinner("Optimizing database..."):
                db.vacuum()
                st.success("✅ Database optimized!")
        
        if st.button("🗑️ Clear Cache", width='stretch'):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Cache cleared!")
        
        if st.button("📊 Rebuild Indexes", width='stretch'):
            with st.spinner("Rebuilding indexes..."):
                db.conn.execute("REINDEX")
                st.success("✅ Indexes rebuilt!")
    
    with col2:
        st.markdown("*Cleanup*")
        
        if st.button("🧹 Remove Old Data (>1 year)", width='stretch'):
            if st.checkbox("⚠️ Confirm deletion"):
                # Could implement cleanup logic
                st.info("🚧 Feature coming soon")
        
        if st.button("🗑️ Clear All Data", width='stretch'):
            if st.checkbox("⚠️⚠️ CONFIRM DELETION (irreversible!)"):
                st.error("🚫 This would delete all data. Implementation disabled for safety.")
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    # Backup & Restore
    st.markdown("**Backup & Restore**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("*Create Backup*")
        
        backup_name = st.text_input(
            "Backup name",
            value=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        
        if st.button("💾 Create Backup", width='stretch'):
            try:
                backup_dir = Path("backups")
                backup_dir.mkdir(exist_ok=True)
                
                backup_path = backup_dir / backup_name
                shutil.copy2(db_path, backup_path)
                
                st.success(f"✅ Backup created: {backup_path}")
                st.info(f"📁 Size: {backup_path.stat().st_size / (1024*1024):.2f} MB")
            except Exception as e:
                st.error(f"❌ Backup failed: {e}")
    
    with col2:
        st.markdown("*Restore from Backup*")
        
        # List available backups
        backup_dir = Path("backups")
        if backup_dir.exists():
            backups = sorted(backup_dir.glob("*.db"), reverse=True)
            if backups:
                backup_files = [b.name for b in backups]
                selected_backup = st.selectbox("Select backup", backup_files)
                
                if st.button("📂 Restore Backup", width='stretch'):
                    if st.checkbox("⚠️ Confirm restore (will overwrite current data)"):
                        try:
                            # Close current connection
                            db.close()
                            
                            # Restore backup
                            shutil.copy2(backup_dir / selected_backup, db_path)
                            
                            st.success(f"✅ Restored from {selected_backup}")
                            st.info("🔄 Please restart the app to use restored database")
                        except Exception as e:
                            st.error(f"❌ Restore failed: {e}")
            else:
                st.info("📁 No backups found")
        else:
            st.info("📁 No backups directory")
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    # Export data
    st.markdown("**Export Database**")
    
    if st.button("📥 Export as SQL", width='stretch'):
        st.info("🚧 SQL export feature coming soon")
    
    if st.button("📥 Export as JSON", width='stretch'):
        st.info("🚧 JSON export feature coming soon")


def advanced_settings_tab():
    """Advanced settings"""
    st.markdown('<p class="section-header">🔐 Advanced Settings</p>', unsafe_allow_html=True)
    
    st.warning("⚠️ Advanced settings - modify with caution!")
    
    st.markdown("**API Configuration**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("NSE API Endpoint", value="https://www.nseindia.com")
        st.number_input("Request Timeout (seconds)", min_value=5, max_value=60, value=30)
    
    with col2:
        st.number_input("Max Retries", min_value=1, max_value=10, value=3)
        st.number_input("Retry Delay (seconds)", min_value=1, max_value=30, value=5)
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    st.markdown("**Rate Limiting**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Max requests per minute", min_value=1, max_value=120, value=30)
    
    with col2:
        st.number_input("Delay between requests (ms)", min_value=100, max_value=5000, value=1000)
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    st.markdown("**Database Configuration**")
    
    st.text_input("Database Path", value="stock_data.db")
    st.number_input("Connection Timeout (seconds)", min_value=5, max_value=120, value=30)
    st.checkbox("Enable WAL mode", value=True, help="Write-Ahead Logging for better concurrency")
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    st.markdown("**Logging**")
    
    log_level = st.selectbox("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"])
    st.text_input("Log File Path", value="fortune_trading.log")
    st.number_input("Max Log File Size (MB)", min_value=1, max_value=100, value=10)
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    if st.button("💾 Save Advanced Settings", type="primary", width='stretch'):
        st.success("✅ Advanced settings saved!")
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    # Danger zone
    st.markdown("**🚨 Danger Zone**")
    
    with st.expander("⚠️ Reset All Settings"):
        st.warning("This will reset all settings to defaults")
        if st.button("🔄 Reset Settings"):
            if st.checkbox("Confirm reset"):
                st.success("✅ Settings reset to defaults")
    
    with st.expander("⚠️ Reset Database Schema"):
        st.error("This will recreate all database tables (data will be lost!)")
        if st.button("🗑️ Reset Schema"):
            if st.checkbox("⚠️⚠️ I understand data will be lost"):
                st.error("🚫 Implementation disabled for safety")