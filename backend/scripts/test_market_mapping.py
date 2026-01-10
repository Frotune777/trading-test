import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
import json

SQLITE_DB_PATH = "/home/fortune/Desktop/Python_Projects/trader_start/data/trading.db"
POSTGRES_URI = "postgresql://postgres:postgres@localhost:5438/quad_trading"

def test_market_migration():
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    engine = create_engine(POSTGRES_URI)
    
    tables = ['market_bulk_deals', 'market_insider_trading', 'market_fii_dii']
    
    for table in tables:
        print(f"\nChecking table: {table}")
        df = pd.read_sql(f"SELECT * FROM {table} LIMIT 5", sqlite_conn)
        print("SQLite columns:", df.columns.tolist())
        print("First row samples:")
        print(df.iloc[0].to_dict())
        
        # Test mapping
        if table == 'market_insider_trading':
             row = df.iloc[0]
             mapping = {
                "symbol": row.get('symbol'),
                "company": row.get('company'),
                "person_name": row.get('acqName'),
                "person_category": row.get('personCategory'),
                "transaction_type": row.get('tdpTransactionType'),
                "securities_type": row.get('secType'),
                "number_of_securities": int(row.get('buyQuantity', 0)) or int(row.get('sellquantity', 0)) or 0,
                "value": float(row.get('buyValue', 0)) or float(row.get('sellValue', 0)) or 0,
                "acquisition_date": pd.to_datetime(row.get('acqfromDt'))
             }
             print("Mapped Insider trading row:", mapping)
             
    sqlite_conn.close()

if __name__ == "__main__":
    test_market_migration()
