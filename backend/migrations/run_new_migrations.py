#!/usr/bin/env python3
"""
Run database migrations for new features
Applies migrations 006, 007, and 008
"""

import psycopg2
from psycopg2 import sql
import os
from pathlib import Path

# Database connection from environment
DB_HOST = os.getenv('POSTGRES_SERVER', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'quad_trading')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')

def run_migration(conn, migration_file):
    """Run a single migration file"""
    print(f"\\nRunning migration: {migration_file.name}")
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    try:
        with conn.cursor() as cur:
            cur.execute(migration_sql)
        conn.commit()
        print(f"✅ Successfully applied {migration_file.name}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error applying {migration_file.name}: {e}")
        return False

def main():
    """Run all pending migrations"""
    print("=" * 60)
    print("Database Migration Runner")
    print("=" * 60)
    
    # Connect to database
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print(f"✅ Connected to database: {DB_NAME}")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return 1
    
    # Get migration files
    migrations_dir = Path(__file__).parent
    migration_files = [
        migrations_dir / "006_add_user_tables.sql",
        migrations_dir / "007_add_action_center_tables.sql",
        migrations_dir / "008_add_monitoring_tables.sql",
        migrations_dir / "011_add_strategy_code_field.sql",
        migrations_dir / "012_ta_aggregator_enhancements.sql",
        migrations_dir / "013_ta_signal_enhancements.sql",
        migrations_dir / "014_risk_management.sql",  # Phase 3: Risk Management
    ]
    
    # Run migrations
    success_count = 0
    for migration_file in migration_files:
        if migration_file.exists():
            if run_migration(conn, migration_file):
                success_count += 1
        else:
            print(f"⚠️  Migration file not found: {migration_file.name}")
    
    # Close connection
    conn.close()
    
    # Summary
    print("\\n" + "=" * 60)
    print(f"Migration Summary: {success_count}/{len(migration_files)} successful")
    print("=" * 60)
    
    return 0 if success_count == len(migration_files) else 1

if __name__ == "__main__":
    exit(main())
