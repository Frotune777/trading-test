"""
Database Migration: Add Action Center Tables
Run this script to create pending_orders and order_approval_logs tables.
"""

from sqlalchemy import text
from app.core.database import sync_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_action_center_tables():
    """Create Action Center tables"""
    
    # SQL for pending_orders table (PostgreSQL)
    pending_orders_sql = """
    CREATE TABLE IF NOT EXISTS pending_orders (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        api_type VARCHAR(50) NOT NULL,
        order_data JSONB NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        created_at_ist TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        approved_at_ist TIMESTAMP WITH TIME ZONE,
        rejected_at_ist TIMESTAMP WITH TIME ZONE,
        executed_at_ist TIMESTAMP WITH TIME ZONE,
        approved_by VARCHAR(255),
        rejected_by VARCHAR(255),
        rejected_reason TEXT,
        broker_order_id VARCHAR(255),
        broker_status VARCHAR(50),
        broker_response JSONB,
        strategy_name VARCHAR(100),
        decision_id VARCHAR(100)
    );
    
    CREATE INDEX IF NOT EXISTS idx_pending_orders_user_id ON pending_orders(user_id);
    CREATE INDEX IF NOT EXISTS idx_pending_orders_status ON pending_orders(status);
    CREATE INDEX IF NOT EXISTS idx_pending_orders_created_at ON pending_orders(created_at_ist);
    CREATE INDEX IF NOT EXISTS idx_pending_orders_user_status ON pending_orders(user_id, status);
    CREATE INDEX IF NOT EXISTS idx_pending_orders_status_created ON pending_orders(status, created_at_ist);
    """
    
    # SQL for order_approval_logs table
    approval_logs_sql = """
    CREATE TABLE IF NOT EXISTS order_approval_logs (
        id SERIAL PRIMARY KEY,
        pending_order_id INTEGER NOT NULL REFERENCES pending_orders(id),
        action VARCHAR(20) NOT NULL,
        performed_by VARCHAR(255) NOT NULL,
        performed_at_ist TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        reason TEXT,
        metadata JSONB
    );
    
    CREATE INDEX IF NOT EXISTS idx_approval_logs_order_id ON order_approval_logs(pending_order_id);
    CREATE INDEX IF NOT EXISTS idx_approval_logs_performed_at ON order_approval_logs(performed_at_ist);
    """
    
    try:
        with sync_engine.connect() as conn:
            # Create pending_orders table
            logger.info("Creating pending_orders table...")
            conn.execute(text(pending_orders_sql))
            conn.commit()
            logger.info("✅ Pending orders table created successfully")
            
            # Create approval_logs table
            logger.info("Creating order_approval_logs table...")
            conn.execute(text(approval_logs_sql))
            conn.commit()
            logger.info("✅ Order approval logs table created successfully")
            
        logger.info("🎉 Action Center migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting Action Center database migration...")
    
    if create_action_center_tables():
        logger.info("\n✅ Action Center is ready!")
        logger.info("Users in 'semi_auto' mode will now have orders queued for approval.")
    else:
        logger.error("Migration failed")
