"""
SQLite to PostgreSQL Migration Script

Migrates all data from SQLite (stock_data.db) to PostgreSQL.
Handles schema creation, data migration, and validation.
"""

import sys
sys.path.insert(0, '/app')

import asyncio
import sqlite3
import pandas as pd
import logging
from typing import List, Dict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import text
from app.core.config import settings
from app.database.models_quad import Base

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Handles migration from SQLite to PostgreSQL"""
    
    def __init__(self, sqlite_path: str = '/app/data/stock_data.db'):
        self.sqlite_path = sqlite_path
        self.sqlite_conn = None
        self.pg_engine = None
        
    async def connect(self):
        """Connect to both databases"""
        logger.info(f"Connecting to SQLite: {self.sqlite_path}")
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row
        
        # Build PostgreSQL URI
        pg_uri = (
            f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_SERVER}:5432/{settings.POSTGRES_DB}"
        )
        logger.info(f"Connecting to PostgreSQL: {settings.POSTGRES_SERVER}:{settings.POSTGRES_DB}")
        self.pg_engine = create_async_engine(pg_uri, echo=False)
        
    async def create_schema(self):
        """Create all tables in PostgreSQL"""
        logger.info("Creating PostgreSQL schema...")
        
        async with self.pg_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ PostgreSQL schema created")
        
    async def get_sqlite_tables(self) -> List[str]:
        """Get list of tables from SQLite"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found {len(tables)} tables in SQLite")
        return tables
        
    async def migrate_table(self, table_name: str) -> Dict:
        """Migrate a single table from SQLite to PostgreSQL"""
        logger.info(f"Migrating table: {table_name}")
        
        try:
            # Read data from SQLite
            df = pd.read_sql(f'SELECT * FROM {table_name}', self.sqlite_conn)
            row_count = len(df)
            
            if row_count == 0:
                logger.info(f"  ⚠️ {table_name}: No data to migrate")
                return {'table': table_name, 'rows': 0, 'status': 'empty'}
            
            logger.info(f"  Read {row_count:,} rows from SQLite")
            
            # Convert datetime columns from strings to datetime objects
            datetime_columns = []
            for col in df.columns:
                if df[col].dtype == 'object' and col.lower().endswith(('_at', 'time', 'date', 'timestamp')):
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                        datetime_columns.append(col)
                    except:
                        pass
            
            if datetime_columns:
                logger.info(f"  Converted datetime columns: {', '.join(datetime_columns)}")
            
            # Convert DataFrame to list of dicts
            records = df.to_dict('records')
            
            # Insert into PostgreSQL in batches
            batch_size = 1000
            total_inserted = 0
            
            async with self.pg_engine.begin() as conn:
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    
                    # Build INSERT statement
                    if batch:
                        columns = list(batch[0].keys())
                        placeholders = ', '.join([f':{col}' for col in columns])
                        cols_str = ', '.join(columns)
                        
                        insert_sql = f"""
                            INSERT INTO {table_name} ({cols_str})
                            VALUES ({placeholders})
                            ON CONFLICT DO NOTHING
                        """
                        
                        await conn.execute(text(insert_sql), batch)
                        total_inserted += len(batch)
                        
                        if (i + batch_size) % 5000 == 0:
                            logger.info(f"  Progress: {total_inserted:,}/{row_count:,} rows")
            
            logger.info(f"  ✅ {table_name}: Migrated {total_inserted:,} rows")
            return {'table': table_name, 'rows': total_inserted, 'status': 'success'}
            
        except Exception as e:
            logger.error(f"  ❌ {table_name}: Migration failed - {e}")
            return {'table': table_name, 'rows': 0, 'status': 'failed', 'error': str(e)}
    
    async def verify_migration(self, table_name: str) -> bool:
        """Verify row counts match between SQLite and PostgreSQL"""
        # SQLite count
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
        sqlite_count = cursor.fetchone()[0]
        
        # PostgreSQL count
        async with self.pg_engine.connect() as conn:
            result = await conn.execute(text(f'SELECT COUNT(*) FROM {table_name}'))
            pg_count = result.scalar()
        
        match = sqlite_count == pg_count
        status = "✅" if match else "❌"
        logger.info(f"  {status} {table_name}: SQLite={sqlite_count:,}, PostgreSQL={pg_count:,}")
        
        return match
    
    async def migrate_all(self):
        """Migrate all tables"""
        logger.info("=" * 60)
        logger.info("STARTING MIGRATION: SQLite → PostgreSQL")
        logger.info("=" * 60)
        
        # Get tables to migrate
        tables = await self.get_sqlite_tables()
        
        # Priority tables first
        priority_tables = [
            'quad_decisions',
            'price_history',
            'companies',
            'indices',
            'technical_indicators',
            'insider_trading',
            'corporate_events',
            'option_chain'
        ]
        
        # Migrate priority tables first
        results = []
        for table in priority_tables:
            if table in tables:
                result = await self.migrate_table(table)
                results.append(result)
        
        # Migrate remaining tables
        remaining_tables = [t for t in tables if t not in priority_tables]
        for table in remaining_tables:
            result = await self.migrate_table(table)
            results.append(result)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 60)
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        empty = [r for r in results if r['status'] == 'empty']
        
        total_rows = sum(r['rows'] for r in successful)
        
        logger.info(f"Total tables: {len(results)}")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")
        logger.info(f"Empty: {len(empty)}")
        logger.info(f"Total rows migrated: {total_rows:,}")
        
        if failed:
            logger.error("\nFailed tables:")
            for r in failed:
                logger.error(f"  - {r['table']}: {r.get('error', 'Unknown error')}")
        
        # Verification
        logger.info("\n" + "=" * 60)
        logger.info("VERIFICATION")
        logger.info("=" * 60)
        
        all_verified = True
        for result in successful:
            table = result['table']
            verified = await self.verify_migration(table)
            if not verified:
                all_verified = False
        
        if all_verified:
            logger.info("\n✅ ALL TABLES VERIFIED SUCCESSFULLY")
        else:
            logger.error("\n❌ SOME TABLES FAILED VERIFICATION")
        
        return all_verified
    
    async def close(self):
        """Close database connections"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_engine:
            await self.pg_engine.dispose()


async def main():
    """Main migration function"""
    migrator = DatabaseMigrator()
    
    try:
        # Connect to databases
        await migrator.connect()
        
        # Create PostgreSQL schema
        await migrator.create_schema()
        
        # Migrate all data
        success = await migrator.migrate_all()
        
        # Close connections
        await migrator.close()
        
        if success:
            logger.info("\n🎉 MIGRATION COMPLETED SUCCESSFULLY")
            sys.exit(0)
        else:
            logger.error("\n⚠️ MIGRATION COMPLETED WITH ERRORS")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"\n❌ MIGRATION FAILED: {e}", exc_info=True)
        await migrator.close()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
