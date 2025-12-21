# dashboard/pages/data_manager.py
"""
Data Manager Page - With Stock Symbol Validation
Fixed: Streamlit deprecation warnings & Table Stats Logic
Version: 3.4 - Production Ready with Validation
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging

from frontend.utils.data_loader import get_database, get_updater, get_nse
from frontend.utils.formatters import format_time_ago

logger = logging.getLogger(__name__)


# ============================================================================
# HTML TABLE RENDERER
# ============================================================================

def render_html_table(df: pd.DataFrame, height: int = None) -> str:
    """Render DataFrame as HTML table with dark theme"""
    
    height_style = f"max-height: {height}px; overflow-y: auto;" if height else ""
    
    html = f"""
    <div style="{height_style} background-color: #161b22; border: 1px solid #2d3748; border-radius: 8px; padding: 0; margin-bottom: 1rem;">
        <table style="width: 100%; border-collapse: collapse; background-color: #161b22; color: #e6edf3;">
            <thead>
                <tr style="background-color: #21262d;">
    """
    
    for col in df.columns:
        html += f'<th style="padding: 12px 8px; text-align: left; color: #4a90e2; font-weight: bold; border-bottom: 2px solid #4a90e2;">{col}</th>'
    
    html += """
                </tr>
            </thead>
            <tbody>
    """
    
    for idx, row in df.iterrows():
        html += '<tr style="background-color: #161b22;" onmouseover="this.style.backgroundColor=\'rgba(74, 144, 226, 0.15)\'" onmouseout="this.style.backgroundColor=\'#161b22\'">'
        for val in row:
            html += f'<td style="padding: 10px 8px; color: #e6edf3; border-bottom: 1px solid #2d3748;">{val}</td>'
        html += '</tr>'
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    return html


# ============================================================================
# STOCK VALIDATION
# ============================================================================

def validate_stock_symbol(symbol: str, nse) -> Tuple[bool, str, Dict]:
    """
    Validate if stock symbol exists on NSE
    
    Returns:
        (is_valid, message, stock_info)
    """
    
    try:
        # Clean symbol
        symbol = symbol.strip().upper()
        
        if not symbol:
            return False, "Empty symbol", {}
        
        # Check symbol format (basic validation)
        if len(symbol) > 20 or len(symbol) < 2:
            return False, f"Invalid symbol length: {len(symbol)} characters", {}
        
        # Special characters check
        if not symbol.replace('-', '').replace('&', '').isalnum():
            return False, f"Invalid characters in symbol: {symbol}", {}
        
        # Try to search in NSE master data
        try:
            search_result = nse.search(symbol, exchange='NSE', match=False)
            
            if search_result is not None and not search_result.empty:
                # Found in NSE database
                stock_info = search_result.iloc[0].to_dict() if len(search_result) > 0 else {}
                return True, f"✅ Valid NSE symbol", stock_info
            
        except Exception as e:
            logger.debug(f"NSE search error for {symbol}: {e}")
        
        # Try to get equity info (more reliable check)
        try:
            equity_info = nse.equity_info(symbol)
            if equity_info:
                return True, "✅ Valid NSE symbol (verified via equity info)", equity_info
        except Exception as e:
            logger.debug(f"Equity info error for {symbol}: {e}")
        
        # Try to get current price
        try:
            price_info = nse.price_info(symbol)
            if price_info:
                return True, "✅ Valid NSE symbol (verified via price)", price_info
        except Exception as e:
            logger.debug(f"Price info error for {symbol}: {e}")
        
        # If all methods fail, symbol likely doesn't exist
        return False, f"❌ Symbol '{symbol}' not found on NSE. Please verify the symbol.", {}
    
    except Exception as e:
        logger.error(f"Validation error for {symbol}: {e}")
        return False, f"⚠️ Validation error: {str(e)}", {}


def batch_validate_symbols(symbols: List[str], nse) -> Dict[str, Tuple[bool, str, Dict]]:
    """
    Validate multiple symbols
    
    Returns:
        Dict mapping symbol to (is_valid, message, info)
    """
    results = {}
    
    for symbol in symbols:
        results[symbol] = validate_stock_symbol(symbol, nse)
    
    return results


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_safe_update_summary(db) -> pd.DataFrame:
    """Safely retrieve update summary"""
    try:
        summary = db.get_update_summary()
        if not summary.empty:
            return summary
    except:
        pass
    
    try:
        query = """
            SELECT 
                symbol,
                MAX(created_at) as last_update,
                COUNT(*) as update_count
            FROM update_log
            GROUP BY symbol
            ORDER BY last_update DESC
        """
        return pd.read_sql_query(query, db.conn)
    except:
        return pd.DataFrame()


def get_sector_statistics(db) -> Dict[str, int]:
    """Get sector counts"""
    companies = db.get_all_companies()
    sector_counts = {}
    for company in companies:
        sector = company.get('sector', 'Unknown')
        if sector:
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
    return sector_counts


def get_data_freshness_distribution(db, companies: List[Dict]) -> Dict[str, int]:
    """Calculate freshness"""
    now = datetime.now()
    distribution = {
        '< 6 hours': 0,
        '6-24 hours': 0,
        '1-7 days': 0,
        '> 7 days': 0,
        'Never': 0
    }
    
    for company in companies:
        last_update = db.get_last_update(company['symbol'])
        if not last_update:
            distribution['Never'] += 1
        else:
            age = now - last_update
            if age < timedelta(hours=6):
                distribution['< 6 hours'] += 1
            elif age < timedelta(hours=24):
                distribution['6-24 hours'] += 1
            elif age < timedelta(days=7):
                distribution['1-7 days'] += 1
            else:
                distribution['> 7 days'] += 1
    
    return distribution


# ============================================================================
# MAIN PAGE
# ============================================================================

def data_manager_page():
    """Main data management dashboard"""
    st.markdown("## 📥 Data Manager")
    
    db = get_database()
    updater = get_updater()
    nse = get_nse()
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "➕ Add New Stock",
        "📥 Download", 
        "🔄 Update", 
        "📊 Stats",
        "📜 Log"
    ])
    
    with tab1:
        add_new_stock_tab(db, updater, nse)
    
    with tab2:
        download_data_tab(db, updater)
    
    with tab3:
        update_database_tab(db, updater)
    
    with tab4:
        database_stats_tab(db)
    
    with tab5:
        update_log_tab(db)


# ============================================================================
# TAB 1: ADD NEW STOCK (WITH VALIDATION)
# ============================================================================

def add_new_stock_tab(db, updater, nse):
    """Add new stocks with validation"""
    st.markdown('<p class="section-header">➕ Add New Stock</p>', unsafe_allow_html=True)
    
    st.info("💡 Add new stocks to your database. Symbols will be validated before download.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Enter Stock Symbols**")
        
        # Single stock input
        single_symbol = st.text_input(
            "Add Single Stock",
            placeholder="e.g., RELIANCE, TCS, INFY",
            help="Enter NSE symbol"
        ).upper().strip()
        
        st.markdown("**OR**")
        
        # Multiple stocks input
        multi_symbols = st.text_area(
            "Add Multiple Stocks",
            placeholder="Enter multiple symbols (comma or newline separated)\ne.g., TCS, INFY, WIPRO, HDFCBANK",
            height=150,
            help="Separate symbols by comma or newline"
        )
        
        # Parse input
        symbols_to_add = []
        
        if single_symbol:
            symbols_to_add.append(single_symbol)
        
        if multi_symbols:
            parsed = [s.strip().upper() for s in multi_symbols.replace('\n', ',').split(',') if s.strip()]
            symbols_to_add.extend(parsed)
        
        # Remove duplicates
        symbols_to_add = list(set(symbols_to_add))
        
        if symbols_to_add:
            st.success(f"✅ {len(symbols_to_add)} symbol(s) entered: {', '.join(symbols_to_add)}")
    
    with col2:
        st.markdown("**Database Info**")
        
        existing_companies = db.get_all_companies()
        existing_symbols = [c['symbol'] for c in existing_companies]
        
        st.metric("Current Stocks", len(existing_symbols))
        
        st.markdown("---")
        
        st.markdown("**Popular Stocks**")
        st.markdown("""
        **IT:** TCS, INFY, WIPRO  
        **Banks:** HDFCBANK, SBIN  
        **Auto:** TATAMOTORS, MARUTI  
        **Pharma:** SUNPHARMA, DRREDDY  
        **Energy:** RELIANCE, ONGC
        """)
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    # Validation and Add buttons
    if symbols_to_add:
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            validate_clicked = st.button("🔍 Validate Symbols", type="secondary", width="stretch")
        
        with col2:
            clear_clicked = st.button("🗑️ Clear Input", width="stretch")
            if clear_clicked:
                st.rerun()
        
        # Validate symbols
        if validate_clicked or 'validation_results' not in st.session_state:
            with st.spinner("Validating symbols on NSE..."):
                validation_results = batch_validate_symbols(symbols_to_add, nse)
                st.session_state.validation_results = validation_results
        
        if 'validation_results' in st.session_state:
            validation_results = st.session_state.validation_results
            
            # Separate valid and invalid
            valid_symbols = [s for s, (valid, _, _) in validation_results.items() if valid]
            invalid_symbols = [s for s, (valid, _, _) in validation_results.items() if not valid]
            
            # Check against existing
            duplicates = [s for s in valid_symbols if s in existing_symbols]
            new_valid = [s for s in valid_symbols if s not in existing_symbols]
            
            # Display validation results
            st.markdown("### 🔍 Validation Results")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("✅ Valid", len(valid_symbols))
            with col_b:
                st.metric("⚠️ Duplicates", len(duplicates))
            with col_c:
                st.metric("❌ Invalid", len(invalid_symbols))
            
            # Show details
            if valid_symbols:
                st.markdown("**✅ Valid Symbols:**")
                for symbol in valid_symbols:
                    is_valid, message, info = validation_results[symbol]
                    status = "🔄 Already in DB" if symbol in existing_symbols else "🆕 New"
                    company_name = info.get('name', info.get('longName', 'N/A'))
                    st.success(f"**{symbol}** - {status} - {company_name}")
            
            if invalid_symbols:
                st.markdown("**❌ Invalid Symbols:**")
                for symbol in invalid_symbols:
                    is_valid, message, info = validation_results[symbol]
                    st.error(f"**{symbol}** - {message}")
                
                st.warning("⚠️ Please verify these symbols on [NSE Website](https://www.nseindia.com/)")
            
            # Add button (only if valid new symbols exist)
            if new_valid:
                st.markdown('<hr>', unsafe_allow_html=True)
                
                col_x, col_y, col_z = st.columns([1, 2, 1])
                with col_y:
                    if st.button(
                        f"➕ Add {len(new_valid)} Stock(s) & Download Data",
                        type="primary",
                        width="stretch"
                    ):
                        add_and_download_stocks(new_valid, existing_symbols, db, updater)
                        # Clear validation state after adding
                        if 'validation_results' in st.session_state:
                            del st.session_state.validation_results
            elif valid_symbols and not new_valid:
                st.info("ℹ️ All valid symbols are already in your database")
            elif not valid_symbols:
                st.error("❌ No valid symbols to add. Please check and try again.")
    
    else:
        st.info("👆 Enter stock symbols above to get started")


def add_and_download_stocks(symbols: List[str], existing: List[str], db, updater):
    """Add validated stocks and download their data"""
    
    st.markdown("---")
    st.markdown(f"### 📥 Downloading Data for {len(symbols)} Stock(s)")
    
    # Download with progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    results = []
    
    for i, symbol in enumerate(symbols):
        status_text.markdown(f"**Processing {i+1}/{len(symbols)}: {symbol}**")
        
        with results_container:
            with st.expander(f"📊 {symbol}", expanded=(i == len(symbols) - 1)):
                result_placeholder = st.empty()
                details_placeholder = st.empty()
                
                try:
                    # Download complete data
                    result = updater.update_stock(symbol, force=True)
                    results.append(result)
                    
                    if result.get('success'):
                        updates = result.get('updates', {})
                        success_count = len([v for v in updates.values() if 'success' in v])
                        
                        result_placeholder.success(
                            f"✅ Successfully added! Downloaded {success_count} data sections in {result.get('execution_time', 0):.2f}s"
                        )
                        
                        # Show download details
                        details_data = []
                        for section, status in updates.items():
                            emoji = "✅" if "success" in status.lower() else "❌" if "error" in status.lower() else "⏭️"
                            details_data.append({
                                '': emoji,
                                'Section': section.replace('_', ' ').title(),
                                'Status': status
                            })
                        
                        if details_data:
                            details_df = pd.DataFrame(details_data)
                            details_placeholder.markdown(
                                render_html_table(details_df),
                                unsafe_allow_html=True
                            )
                    
                    elif result.get('skipped'):
                        result_placeholder.info(f"⏭️ Skipped: {result.get('message')}")
                    
                    else:
                        errors = result.get('errors', [])
                        result_placeholder.error(f"❌ Failed: {', '.join(errors)}")
                
                except Exception as e:
                    result_placeholder.error(f"💥 Error: {str(e)}")
                    results.append({'symbol': symbol, 'success': False, 'error': str(e)})
        
        progress_bar.progress((i + 1) / len(symbols))
        time.sleep(1.5)  # Rate limiting
    
    progress_bar.empty()
    status_text.empty()
    
    # Summary
    st.markdown('<hr>', unsafe_allow_html=True)
    successful = len([r for r in results if r.get('success')])
    
    if successful == len(symbols):
        st.success(f"🎉 Successfully added all {successful} stocks!")
        st.balloons()
    elif successful > 0:
        st.warning(f"⚠️ Added {successful} out of {len(symbols)} stocks")
    else:
        st.error("❌ Failed to add stocks. Please check the errors above.")
    
    if successful > 0:
        st.info("💡 Go to **Analytics** tab to view your newly added stocks!")


# ============================================================================
# TAB 2: DOWNLOAD (Fixed deprecation)
# ============================================================================

def download_data_tab(db, updater):
    """Bulk download interface"""
    st.markdown('<p class="section-header">📥 Download Data</p>', unsafe_allow_html=True)
    
    st.info("💡 Update data for stocks already in your database")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        preset_lists = {
            "All Stocks": [],
            "NIFTY 50": ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"],
            "IT Sector": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM"],
            "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK"],
            "Custom": []
        }
        
        list_type = st.selectbox("Select List", list(preset_lists.keys()))
        
        companies = db.get_all_companies()
        all_symbols = [c['symbol'] for c in companies]
        
        if list_type == "All Stocks":
            symbols = all_symbols
            st.info(f"📋 All {len(symbols)} stocks")
        elif list_type == "Custom":
            symbols_input = st.text_area("Symbols (comma separated)", "RELIANCE, TCS")
            symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
            symbols = [s for s in symbols if s in all_symbols]
            st.info(f"📋 {len(symbols)} stocks")
        else:
            symbols = [s for s in preset_lists[list_type] if s in all_symbols]
            st.info(f"📋 {len(symbols)} stocks")
    
    with col2:
        st.markdown("**Options**")
        force = st.checkbox("Force update", False)
        delay = st.slider("Delay (sec)", 1.0, 10.0, 2.0, 0.5)
    
    if st.button("📥 Download", type="primary", width="stretch"):
        if symbols:
            download_stocks(symbols, force, delay, updater)
        else:
            st.error("❌ No symbols")


# ============================================================================
# TAB 3: UPDATE (Fixed deprecation)
# ============================================================================

def update_database_tab(db, updater):
    """Update operations"""
    st.markdown('<p class="section-header">🔄 Update</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Quick Actions**")
        
        companies = db.get_all_companies()
        total = len(companies)
        stale = len([c for c in companies if db.needs_update(c['symbol'], hours=24)])
        
        st.metric("Total", total)
        st.metric("Stale", stale)
        
        st.markdown("---")
        
        if st.button("🔄 Update All", width="stretch"):
            if total > 0 and st.checkbox("⚠️ Confirm"):
                update_all_stocks(companies, updater)
        
        if st.button(f"⏰ Update Stale ({stale})", width="stretch"):
            if stale > 0:
                update_stale_stocks(24, updater)
            else:
                st.success("✅ All current")
    
    with col2:
        st.markdown("**Recent**")
        summary = get_safe_update_summary(db)
        
        if not summary.empty:
            recent_data = []
            for _, row in summary.head(10).iterrows():
                symbol = row.get('symbol', '?')
                last = row.get('last_update')
                age = format_time_ago(pd.to_datetime(last)) if pd.notna(last) else 'Never'
                count = row.get('update_count', 0)
                
                status = '🟢' if 'h' in age else '🟡' if 'd' in age else '🔴'
                
                recent_data.append({
                    '': status,
                    'Symbol': symbol,
                    'Last': age,
                    'Count': int(count)
                })
            
            recent_df = pd.DataFrame(recent_data)
            st.markdown(render_html_table(recent_df, height=300), unsafe_allow_html=True)
        else:
            st.info("No history")


# ============================================================================
# TAB 4: STATS (MODIFIED)
# ============================================================================

def database_stats_tab(db):
    """Statistics"""
    st.markdown('<p class="section-header">📊 Statistics</p>', unsafe_allow_html=True)
    
    stats = db.get_database_stats()
    companies = db.get_all_companies()
    
    # -------------------------------------------------------------
    # 🎯 FIX: Retrieve the pre-fetched and detailed statistics from session state
    table_stats_from_session = st.session_state.get('table_statistics')
    # -------------------------------------------------------------
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Size", f"{stats['database_size']:.2f} MB")
    with col2:
        st.metric("Companies", len(companies))
    with col3:
        st.metric("Records", f"{stats['table_counts'].get('price_history', 0):,}")
    with col4:
        st.metric("Tables", len(stats['table_counts']))
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    st.markdown("**📊 Table Statistics**")
    
    if table_stats_from_session is not None:
        # Use the data that was already processed by utils/data_status.py
        table_data = []
        # stats is a list of tuples: (table_name, count, status_emoji, quality_emoji)
        for table, count, status, quality in table_stats_from_session:
            table_data.append({
                'Table': table,
                'Records': f"{count:,}", 
                'Status': status,
                'Quality': quality
            })
        
        # Sort by Table name for consistency
        df = pd.DataFrame(table_data).sort_values(by='Table', ascending=True)
        
    else:
        # Fallback to the original logic if session state is somehow empty
        st.warning("⚠️ Detailed statistics not found in session state. Using basic fallback logic.")
        table_data = []
        for table, count in sorted(stats['table_counts'].items()):
            status = '✅ Active' if count > 0 else '⚪ Empty'
            quality = '🟢 Rich' if count > 1000 else '🟡 Good' if count > 100 else '🟠 Limited' if count > 0 else '⚪ Empty'
            table_data.append({
                'Table': table,
                'Records': f"{count:,}",
                'Status': status,
                'Quality': quality
            })
        df = pd.DataFrame(table_data)


    st.markdown(render_html_table(df, height=400), unsafe_allow_html=True)
    
    st.markdown('<hr>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏢 Sectors**")
        sector_counts = get_sector_statistics(db)
        total = len(companies)
        
        sector_data = []
        for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total * 100) if total > 0 else 0
            sector_data.append({
                'Sector': sector,
                'Count': count,
                '%': f"{pct:.1f}%"
            })
        
        sector_df = pd.DataFrame(sector_data)
        st.markdown(render_html_table(sector_df, height=300), unsafe_allow_html=True)
    
    with col2:
        st.markdown("**⏰ Freshness**")
        freshness = get_data_freshness_distribution(db, companies)
        
        fresh_data = []
        for age, count in freshness.items():
            pct = (count / total * 100) if total > 0 else 0
            emoji = '🟢' if '< 6' in age else '🟡' if '6-24' in age else '🟠' if '1-7' in age else '🔴'
            
            fresh_data.append({
                '': emoji,
                'Age': age,
                'Count': count,
                '%': f"{pct:.1f}%"
            })
        
        fresh_df = pd.DataFrame(fresh_data)
        st.markdown(render_html_table(fresh_df, height=300), unsafe_allow_html=True)


# ============================================================================
# TAB 5: LOG (Fixed deprecation - no buttons here)
# ============================================================================

def update_log_tab(db):
    """Update log"""
    st.markdown('<p class="section-header">📜 Log</p>', unsafe_allow_html=True)
    
    companies = db.get_all_companies()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        symbol = st.selectbox("Symbol", ['All'] + sorted([c['symbol'] for c in companies]))
    with col2:
        status = st.selectbox("Status", ['All', 'success', 'error'])
    with col3:
        period = st.selectbox("Period", ['Last 24h', 'Last 7 days', 'Last 30 days', 'All'])
    with col4:
        limit = st.number_input("Records", 10, 1000, 100)
    
    query = "SELECT * FROM update_log WHERE 1=1"
    params = []
    
    if symbol != 'All':
        query += " AND symbol = ?"
        params.append(symbol)
    
    if status != 'All':
        query += " AND status = ?"
        params.append(status)
    
    if period != 'All':
        days = {'Last 24h': 1, 'Last 7 days': 7, 'Last 30 days': 30}.get(period, 999)
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        query += " AND created_at >= ?"
        params.append(cutoff)
    
    query += f" ORDER BY created_at DESC LIMIT {limit}"
    
    try:
        log_df = pd.read_sql_query(query, db.conn, params=params)
        
        if not log_df.empty:
            log_df['age'] = log_df['created_at'].apply(lambda x: format_time_ago(pd.to_datetime(x)))
            log_df[''] = log_df['status'].apply(lambda x: '✅' if x == 'success' else '❌')
            
            display = log_df[['', 'symbol', 'table_name', 'age']].rename(columns={
                'symbol': 'Symbol',
                'table_name': 'Table',
                'age': 'When'
            })
            
            st.markdown(render_html_table(display), unsafe_allow_html=True)
            
            st.markdown('<hr>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("✅", len(log_df[log_df['status'] == 'success']))
            with col2:
                st.metric("❌", len(log_df[log_df['status'] == 'error']))
            with col3:
                avg = log_df['execution_time'].mean() if 'execution_time' in log_df.columns else 0
                st.metric("⏱️", f"{avg:.1f}s" if pd.notna(avg) else "N/A")
            with col4:
                rate = len(log_df[log_df['status'] == 'success']) / len(log_df) * 100
                st.metric("📊", f"{rate:.0f}%")
        else:
            st.info("No logs")
    except Exception as e:
        st.error(f"Error: {e}")


# ============================================================================
# HELPERS (Fixed deprecation)
# ============================================================================

def download_stocks(symbols, force, delay, updater):
    """Batch download"""
    progress = st.progress(0)
    status = st.empty()
    results = []
    
    for i, symbol in enumerate(symbols):
        status.text(f"{i+1}/{len(symbols)}: {symbol}")
        
        with st.expander(f"📊 {symbol}", expanded=(i == len(symbols) - 1)):
            try:
                result = updater.update_stock(symbol, force=force)
                results.append(result)
                
                if result.get('success'):
                    st.success(f"✅ Done in {result.get('execution_time', 0):.1f}s")
                elif result.get('skipped'):
                    st.info("⏭️ Skipped")
                else:
                    st.error("❌ Failed")
            except Exception as e:
                st.error(f"💥 {e}")
        
        progress.progress((i + 1) / len(symbols))
        if i < len(symbols) - 1:
            time.sleep(delay)
    
    status.empty()
    progress.empty()
    show_summary(results)


def update_all_stocks(companies, updater):
    download_stocks([c['symbol'] for c in companies], True, 2.0, updater)


def update_stale_stocks(hours, updater):
    with st.spinner("Finding stale..."):
        result = updater.update_stale_stocks(hours=hours)
    if result:
        show_summary(result)


def show_summary(results):
    """Show summary"""
    if isinstance(results, dict):
        results = list(results.values())
    
    total = len(results)
    success = len([r for r in results if r.get('success')])
    
    st.markdown("### 📊 Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("✅ Success", success)
    
    rate = (success / total * 100) if total > 0 else 0
    if rate == 100:
        st.success("🎉 Perfect!")
    elif rate >= 90:
        st.success(f"✅ {rate:.0f}%")
    else:
        st.warning(f"⚠️ {rate:.0f}%")

if __name__ == "__main__":
    data_manager_page()