import sqlite3

def inspect_db(db_path):
    print(f"\n--- Inspecting {db_path} ---")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [col[1] for col in cursor.fetchall()]
            print(" | ".join(columns))
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            for row in rows:
                print(" | ".join(str(item) for item in row))
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

inspect_db("backend/stock_data.db")
inspect_db("stock_data.db")

inspect_db("backend/stock_data.db")
inspect_db("stock_data.db")
