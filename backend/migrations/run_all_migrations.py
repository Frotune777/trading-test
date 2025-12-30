#!/usr/bin/env python3
import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env if it exists
env_path = Path('.') / '.env'
logger.info(f"Looking for .env at: {env_path.absolute()}")
load_dotenv(dotenv_path=env_path)

# Database connection from environment
# Check different common environment variable names
DB_HOST = os.getenv('POSTGRES_SERVER', os.getenv('DB_HOST', 'localhost'))
DB_PORT = os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'quad_trading'))
DB_USER = os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'postgres'))
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', os.getenv('DB_PASSWORD', 'postgres'))

def run_migration(conn, migration_file):
    logger.info(f"Applying migration: {migration_file.name}")
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        logger.info(f"✅ Successfully applied {migration_file.name}")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error applying {migration_file.name}: {e}")
        return False

def main():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logger.info(f"Connected to database: {DB_NAME}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return 1

    migrations_dir = Path(__file__).parent
    migration_files = sorted(list(migrations_dir.glob("*.sql")))
    
    success_count = 0
    for migration_file in migration_files:
        if run_migration(conn, migration_file):
            success_count += 1
    
    conn.close()
    logger.info(f"Migration Summary: {success_count}/{len(migration_files)} successful")
    return 0 if success_count == len(migration_files) else 1

if __name__ == "__main__":
    exit(main())
