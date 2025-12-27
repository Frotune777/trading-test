"""
Run database migration for QUAD v2
"""
import sqlite3
import os

# Read migration SQL
migration_file = 'migrations/005_quad_decisions_v2.sql'
with open(migration_file, 'r') as f:
    migration_sql = f.read()

# Connect to database
db_path = os.getenv('SQLITE_DB_PATH', 'stock_data.db')
conn = sqlite3.connect(db_path)

try:
    # Execute migration
    conn.executescript(migration_sql)
    conn.commit()
    print(f"✅ Migration executed successfully")
    
    # Verify table exists
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quad_decisions_v2'")
    result = cursor.fetchone()
    
    if result:
        print(f"✅ Table 'quad_decisions_v2' created successfully")
        
        # Get column count
        cursor = conn.execute("PRAGMA table_info(quad_decisions_v2)")
        columns = cursor.fetchall()
        print(f"✅ Table has {len(columns)} columns")
    else:
        print("❌ Table 'quad_decisions_v2' not found")
        
except Exception as e:
    print(f"❌ Migration failed: {e}")
    conn.rollback()
finally:
    conn.close()
