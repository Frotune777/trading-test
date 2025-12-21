import sqlite3
import pandas as pd
from pathlib import Path
import os
import sys

# Add parent directory to python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

DB_PATH = 'stock_data.db'

def analyze_database(db_path):
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    
    # Get all tables
    tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(tables_query, conn)['name'].tolist()
    
    print(f"📊 Analyzing Database: {db_path}")
    print(f"Found {len(tables)} tables.\n")
    
    stats = []
    
    for table in tables:
        count_query = f"SELECT COUNT(*) as count FROM {table}"
        try:
            count = pd.read_sql_query(count_query, conn).iloc[0]['count']
            
            # Check for nulls in key columns if table is not empty
            null_info = "N/A"
            if count > 0:
                # Sample a few rows to check for nulls in typical columns
                sample_query = f"SELECT * FROM {table} LIMIT 100"
                df = pd.read_sql_query(sample_query, conn)
                null_cols = df.columns[df.isnull().any()].tolist()
                if null_cols:
                    null_info = f"Nulls in: {', '.join(null_cols[:3])}..."
                else:
                    null_info = "No nulls in sample"
            
            stats.append({
                'Table': table,
                'Row Count': count,
                'Status': null_info
            })
        except Exception as e:
            stats.append({
                'Table': table,
                'Row Count': 'Error',
                'Status': str(e)
            })
            
    stats_df = pd.DataFrame(stats)
    print(stats_df.to_markdown(index=False))
    
    # Deep dive into key tables
    print("\n🔍 Deep Dive:")
    
    # 1. Companies without Price History
    if 'companies' in tables and 'price_history' in tables:
        query = """
        SELECT c.symbol 
        FROM companies c 
        LEFT JOIN price_history p ON c.symbol = p.symbol 
        WHERE p.symbol IS NULL
        """
        missing_price = pd.read_sql_query(query, conn)
        print(f"\nCompanies with NO Price History: {len(missing_price)}")
        if len(missing_price) > 0:
            print(f"Examples: {', '.join(missing_price['symbol'].head(5).tolist())}")

    # 2. Companies without Fundamental Data
    if 'companies' in tables and 'quarterly_results' in tables:
        query = """
        SELECT c.symbol 
        FROM companies c 
        LEFT JOIN quarterly_results q ON c.symbol = q.symbol 
        WHERE q.symbol IS NULL
        """
        missing_funds = pd.read_sql_query(query, conn)
        print(f"\nCompanies with NO Quarterly Results: {len(missing_funds)}")
        if len(missing_funds) > 0:
            print(f"Examples: {', '.join(missing_funds['symbol'].head(5).tolist())}")
            
    conn.close()

if __name__ == "__main__":
    analyze_database(DB_PATH)
