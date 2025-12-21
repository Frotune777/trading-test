"""
Database Explorer - View and query database directly from dashboard
"""

import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import json

def database_explorer_page():
    """Database Explorer - Browse tables and run SQL queries"""
    
    st.markdown("# 🗄️ Database Explorer")
    st.markdown("Browse tables, run SQL queries, and export data")
    
    # Database path
    db_path = Path('stock_data.db')
    
    if not db_path.exists():
        st.error("❌ Database not found! Please ensure stock_data.db exists.")
        return
    
    # Create connection
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Sidebar for navigation
    with st.sidebar:
        st.markdown("### 🧭 Explorer Options")
        
        explorer_mode = st.radio(
            "Select Mode",
            ["📊 Browse Tables", "🔍 SQL Query", "📋 Schema Viewer", "📈 Quick Stats"]
        )
        
        st.markdown("---")
        
        # Quick database info
        st.markdown("### 📊 Database Info")
        
        # Get database size
        db_size = db_path.stat().st_size / (1024 * 1024)  # MB
        st.metric("Size", f"{db_size:.2f} MB")
        
        # Count tables
        cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        st.metric("Tables", table_count)
        
        # Count total records
        cursor = conn.execute("""
            SELECT SUM(cnt) as total FROM (
                SELECT COUNT(*) as cnt FROM companies
                UNION ALL SELECT COUNT(*) FROM price_history
                UNION ALL SELECT COUNT(*) FROM latest_snapshot
            )
        """)
        total_records = cursor.fetchone()[0] or 0
        st.metric("Total Records", f"{total_records:,}")
    
    # Main content area
    if explorer_mode == "📊 Browse Tables":
        browse_tables_tab(conn)
    elif explorer_mode == "🔍 SQL Query":
        sql_query_tab(conn)
    elif explorer_mode == "📋 Schema Viewer":
        schema_viewer_tab(conn)
    elif explorer_mode == "📈 Quick Stats":
        quick_stats_tab(conn)
    
    # Close connection
    conn.close()


def browse_tables_tab(conn):
    """Browse database tables"""
    
    st.markdown("## 📊 Browse Tables")
    st.markdown("Select a table to view its data")
    
    # Get list of tables
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    # Table categories for better organization
    categories = {
        "📈 Price Data": ["price_history", "intraday_prices", "latest_snapshot"],
        "🏢 Company Info": ["companies", "peers", "shareholding"],
        "💰 Fundamentals": ["quarterly_results", "annual_results", "balance_sheet", "cash_flow", "financial_ratios"],
        "🎯 Market Activity": ["bulk_deals", "block_deals", "insider_trading", "fii_dii_activity"],
        "📊 Derivatives": ["futures_data", "option_chain", "option_chain_summary"],
        "📉 Market Data": ["market_breadth", "gainers_losers", "pre_market_data", "market_depth"],
        "🗂️ System": ["update_log", "data_sources", "custom_metrics", "ml_features"]
    }
    
    # Create tabs for categories
    category_tabs = st.tabs(list(categories.keys()))
    
    for idx, (category, table_list) in enumerate(categories.items()):
        with category_tabs[idx]:
            # Filter tables that exist
            existing_tables = [t for t in table_list if t in tables]
            
            if not existing_tables:
                st.info(f"No tables in {category}")
                continue
            
            # Table selector
            selected_table = st.selectbox(
                "Select table",
                existing_tables,
                key=f"table_select_{category}"
            )
            
            if selected_table:
                display_table_data(conn, selected_table)


def display_table_data(conn, table_name):
    """Display data from a selected table"""
    
    # Get row count
    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    
    # Display controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.metric(f"📊 {table_name}", f"{row_count:,} records")
    
    with col2:
        limit = st.number_input("Rows to display", min_value=10, max_value=1000, value=100, key=f"limit_{table_name}")
    
    with col3:
        sort_order = st.selectbox("Sort", ["DESC", "ASC"], key=f"sort_{table_name}")
    
    with col4:
        if st.button("🔄 Refresh", key=f"refresh_{table_name}"):
            st.rerun()
    
    # Get columns
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Build query based on table type
    if 'date' in columns:
        order_col = 'date'
    elif 'created_at' in columns:
        order_col = 'created_at'
    elif 'updated_at' in columns:
        order_col = 'updated_at'
    elif 'id' in columns:
        order_col = 'id'
    else:
        order_col = columns[0]
    
    # Fetch data
    query = f"SELECT * FROM {table_name} ORDER BY {order_col} {sort_order} LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    
    if not df.empty:
        # Show filters for key columns
        if 'symbol' in df.columns:
            unique_symbols = df['symbol'].dropna().unique()
            if len(unique_symbols) > 1:
                selected_symbol = st.selectbox(
                    "Filter by symbol",
                    ["All"] + list(unique_symbols),
                    key=f"symbol_filter_{table_name}"
                )
                if selected_symbol != "All":
                    df = df[df['symbol'] == selected_symbol]
        
        # Display data
        st.dataframe(
            df,
            use_container_width=True,
            height=400
        )
        
        # Export options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download CSV",
                csv,
                f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                key=f"download_csv_{table_name}"
            )
        
        with col2:
            # Create Excel download
            excel_buffer = pd.ExcelWriter('temp.xlsx', engine='xlsxwriter')
            df.to_excel(excel_buffer, index=False, sheet_name=table_name)
            # Note: For production, use io.BytesIO() instead
        
        with col3:
            json_str = df.to_json(orient='records', indent=2)
            st.download_button(
                "📥 Download JSON",
                json_str,
                f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json",
                key=f"download_json_{table_name}"
            )
    else:
        st.info(f"No data in {table_name}")


def sql_query_tab(conn):
    """SQL Query executor"""
    
    st.markdown("## 🔍 SQL Query")
    st.markdown("Run custom SQL queries on your database")
    
    # Predefined queries
    st.markdown("### 📝 Quick Queries")
    
    quick_queries = {
        "Latest prices for all stocks": """
            SELECT c.symbol, c.company_name, c.sector, 
                   ls.current_price, ls.change_percent, ls.volume, ls.market_cap
            FROM companies c
            LEFT JOIN latest_snapshot ls ON c.symbol = ls.symbol
            ORDER BY ls.change_percent DESC
        """,
        
        "Top gainers today": """
            SELECT symbol, current_price, change_percent, volume
            FROM latest_snapshot
            WHERE change_percent > 0
            ORDER BY change_percent DESC
            LIMIT 10
        """,
        
        "Recent quarterly results": """
            SELECT c.symbol, c.company_name, qr.quarter, 
                   qr.sales, qr.net_profit, qr.eps
            FROM quarterly_results qr
            JOIN companies c ON qr.symbol = c.symbol
            ORDER BY qr.quarter DESC
            LIMIT 20
        """,
        
        "Peer comparison": """
            SELECT p.*, c.company_name
            FROM peers p
            LEFT JOIN companies c ON p.peer_symbol = c.symbol
            ORDER BY p.market_cap DESC
        """,
        
        "Price history summary": """
            SELECT symbol, 
                   COUNT(*) as days_of_data,
                   MIN(date) as first_date,
                   MAX(date) as last_date,
                   MIN(low) as all_time_low,
                   MAX(high) as all_time_high
            FROM price_history
            GROUP BY symbol
        """,
        
        "Database statistics": """
            SELECT 
                'companies' as table_name, COUNT(*) as record_count FROM companies
            UNION ALL SELECT 'price_history', COUNT(*) FROM price_history
            UNION ALL SELECT 'quarterly_results', COUNT(*) FROM quarterly_results
            UNION ALL SELECT 'annual_results', COUNT(*) FROM annual_results
            UNION ALL SELECT 'shareholding', COUNT(*) FROM shareholding
            UNION ALL SELECT 'peers', COUNT(*) FROM peers
            ORDER BY record_count DESC
        """
    }
    
    selected_query = st.selectbox(
        "Select a predefined query",
        ["Custom"] + list(quick_queries.keys())
    )
    
    if selected_query != "Custom":
        query = quick_queries[selected_query]
    else:
        query = ""
    
    # Query editor
    st.markdown("### 💻 SQL Editor")
    
    sql_query = st.text_area(
        "Enter SQL Query",
        value=query,
        height=200,
        help="Write your SQL query here. Use Ctrl+Enter to run."
    )
    
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        run_query = st.button("▶️ Run Query", type="primary", use_container_width=True)
    
    with col2:
        clear_query = st.button("🗑️ Clear", use_container_width=True)
    
    if clear_query:
        st.rerun()
    
    if run_query and sql_query:
        try:
            # Security check - only allow SELECT statements
            if not sql_query.strip().upper().startswith('SELECT'):
                st.error("⚠️ Only SELECT queries are allowed for safety!")
                return
            
            # Execute query
            with st.spinner("Executing query..."):
                df = pd.read_sql_query(sql_query, conn)
            
            # Display results
            st.markdown("### 📊 Results")
            
            if not df.empty:
                st.success(f"✅ Query returned {len(df)} rows")
                
                # Display dataframe
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=400
                )
                
                # Download results
                col1, col2 = st.columns(2)
                
                with col1:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Download Results (CSV)",
                        csv,
                        f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
                
                with col2:
                    json_str = df.to_json(orient='records', indent=2)
                    st.download_button(
                        "📥 Download Results (JSON)",
                        json_str,
                        f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        "application/json"
                    )
            else:
                st.info("Query returned no results")
            
        except Exception as e:
            st.error(f"❌ Query Error: {e}")
            
            # Show helpful error info
            with st.expander("🐛 Error Details"):
                st.code(str(e))
                st.markdown("""
                **Common issues:**
                - Check table names (case sensitive)
                - Verify column names
                - Ensure proper SQL syntax
                - Check for typos
                """)


def schema_viewer_tab(conn):
    """View database schema"""
    
    st.markdown("## 📋 Schema Viewer")
    st.markdown("Explore table structures and relationships")
    
    # Get all tables
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    # Table selector
    selected_table = st.selectbox("Select table to view schema", tables)
    
    if selected_table:
        # Get table info
        cursor = conn.execute(f"PRAGMA table_info({selected_table})")
        columns = cursor.fetchall()
        
        # Create DataFrame for display
        schema_df = pd.DataFrame(columns, columns=['cid', 'name', 'type', 'notnull', 'default', 'pk'])
        schema_df = schema_df[['name', 'type', 'notnull', 'default', 'pk']]
        schema_df['notnull'] = schema_df['notnull'].map({0: 'No', 1: 'Yes'})
        schema_df['pk'] = schema_df['pk'].map({0: '', 1: '🔑 PRIMARY KEY'})
        
        # Display schema
        st.markdown(f"### Table: `{selected_table}`")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.dataframe(
                schema_df,
                use_container_width=True,
                hide_index=True
            )
        
        with col2:
            # Get indexes
            cursor = conn.execute(f"PRAGMA index_list({selected_table})")
            indexes = cursor.fetchall()
            
            st.markdown("#### 📑 Indexes")
            if indexes:
                for idx in indexes:
                    st.text(f"• {idx[1]}")
            else:
                st.text("No indexes")
            
            # Get foreign keys
            cursor = conn.execute(f"PRAGMA foreign_key_list({selected_table})")
            fks = cursor.fetchall()
            
            st.markdown("#### 🔗 Foreign Keys")
            if fks:
                for fk in fks:
                    st.text(f"• {fk[3]} → {fk[2]}.{fk[4]}")
            else:
                st.text("No foreign keys")
        
        # Show CREATE statement
        with st.expander("📝 CREATE TABLE Statement"):
            cursor = conn.execute(f"SELECT sql FROM sqlite_master WHERE name='{selected_table}'")
            create_sql = cursor.fetchone()[0]
            st.code(create_sql, language='sql')


def quick_stats_tab(conn):
    """Quick database statistics"""
    
    st.markdown("## 📈 Quick Statistics")
    
    # Overall stats
    st.markdown("### 📊 Database Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cursor = conn.execute("SELECT COUNT(*) FROM companies")
        companies_count = cursor.fetchone()[0]
        st.metric("Companies", companies_count)
    
    with col2:
        cursor = conn.execute("SELECT COUNT(*) FROM price_history")
        price_records = cursor.fetchone()[0]
        st.metric("Price Records", f"{price_records:,}")
    
    with col3:
        cursor = conn.execute("SELECT COUNT(DISTINCT sector) FROM companies WHERE sector IS NOT NULL")
        sectors = cursor.fetchone()[0]
        st.metric("Sectors", sectors)
    
    with col4:
        cursor = conn.execute("SELECT COUNT(*) FROM update_log WHERE status='success'")
        updates = cursor.fetchone()[0]
        st.metric("Updates", updates)
    
    # Data freshness
    st.markdown("### ⏰ Data Freshness")
    
    freshness_query = """
        SELECT 
            symbol,
            MAX(created_at) as last_update,
            julianday('now') - julianday(MAX(created_at)) as days_old
        FROM update_log
        WHERE status = 'success'
        GROUP BY symbol
        ORDER BY last_update DESC
    """
    
    freshness_df = pd.read_sql_query(freshness_query, conn)
    
    if not freshness_df.empty:
        # Categorize by freshness
        fresh = len(freshness_df[freshness_df['days_old'] < 1])
        stale = len(freshness_df[freshness_df['days_old'] >= 1])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🟢 Fresh (<24h)", fresh)
        with col2:
            st.metric("🔴 Stale (>24h)", stale)
        
        # Show table
        st.dataframe(
            freshness_df[['symbol', 'last_update', 'days_old']].head(20),
            use_container_width=True
        )
    
    # Table sizes
    st.markdown("### 💾 Table Sizes")
    
    size_query = """
        SELECT 
            name as table_name,
            (SELECT COUNT(*) FROM sqlite_master sm WHERE sm.name = m.name) as row_count
        FROM sqlite_master m
        WHERE type = 'table'
        ORDER BY name
    """
    
    # Get actual counts for main tables
    table_counts = []
    main_tables = ['companies', 'price_history', 'quarterly_results', 'annual_results', 
                   'shareholding', 'peers', 'latest_snapshot']
    
    for table in main_tables:
        try:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_counts.append({'Table': table, 'Records': count})
        except:
            pass
    
    if table_counts:
        counts_df = pd.DataFrame(table_counts)
        counts_df = counts_df.sort_values('Records', ascending=False)
        
        # Create bar chart
        st.bar_chart(counts_df.set_index('Table')['Records'])
        
        # Show table
        st.dataframe(counts_df, use_container_width=True, hide_index=True)


# ============================================================================
# INTEGRATION INTO MAIN APP
# ============================================================================

# Export the page function
__all__ = ['database_explorer_page']