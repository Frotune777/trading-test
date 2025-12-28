#!/usr/bin/env python3
"""
Migration script for monitoring tables
Creates latency_metrics, api_traffic, error_logs, pnl_snapshots, trade_performance, system_health
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import sync_engine
from app.database.models_monitoring import Base

def create_monitoring_tables():
    """Create monitoring tables"""
    print("🔧 Creating monitoring tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=sync_engine)
        
        print("✅ Monitoring tables created successfully!")
        print("\nTables created:")
        print("  - latency_metrics")
        print("  - api_traffic")
        print("  - error_logs")
        print("  - pnl_snapshots")
        print("  - trade_performance")
        print("  - system_health")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_tables():
    """Verify tables were created"""
    print("\n🔍 Verifying tables...")
    
    try:
        with sync_engine.connect() as conn:
            # Check each table
            tables = [
                'latency_metrics',
                'api_traffic',
                'error_logs',
                'pnl_snapshots',
                'trade_performance',
                'system_health'
            ]
            
            for table in tables:
                result = conn.execute(text(
                    f"SELECT COUNT(*) FROM information_schema.tables "
                    f"WHERE table_name = '{table}'"
                ))
                count = result.scalar()
                
                if count > 0:
                    print(f"  ✅ {table}")
                else:
                    print(f"  ❌ {table} - NOT FOUND")
        
        print("\n✅ Verification complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Monitoring Tables Migration")
    print("=" * 60)
    print()
    
    # Create tables
    if create_monitoring_tables():
        # Verify
        verify_tables()
        print("\n✅ Migration complete!")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
