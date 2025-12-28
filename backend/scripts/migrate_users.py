"""
Database Migration: Add Users Table with Argon2/Fernet Security
Run this script to create the users and user_sessions tables.
"""

from sqlalchemy import text
from app.core.database import sync_engine, SessionLocalSync
from app.database.models_user import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_users_tables():
    """Create users and user_sessions tables"""
    
    # SQL for users table (PostgreSQL)
    users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE,
        password_hash TEXT NOT NULL,
        api_key_hash TEXT,
        api_key_encrypted TEXT,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
        order_mode VARCHAR(20) NOT NULL DEFAULT 'auto',
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP WITH TIME ZONE
    );
    
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
    CREATE INDEX IF NOT EXISTS idx_users_order_mode ON users(order_mode);
    """
    
    # SQL for user_sessions table
    sessions_table_sql = """
    CREATE TABLE IF NOT EXISTS user_sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        session_token_hash TEXT NOT NULL,
        ip_address VARCHAR(45),
        user_agent TEXT,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        last_activity TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        revoked_at TIMESTAMP WITH TIME ZONE
    );
    
    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_is_active ON user_sessions(is_active);
    CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);
    """
    
    try:
        with sync_engine.connect() as conn:
            # Create users table
            logger.info("Creating users table...")
            conn.execute(text(users_table_sql))
            conn.commit()
            logger.info("✅ Users table created successfully")
            
            # Create sessions table
            logger.info("Creating user_sessions table...")
            conn.execute(text(sessions_table_sql))
            conn.commit()
            logger.info("✅ User sessions table created successfully")
            
        logger.info("🎉 Database migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def create_default_admin():
    """Create default admin user"""
    from app.services.user_auth_service import UserAuthService
    
    try:
        db = SessionLocalSync()
        auth_service = UserAuthService(db)
        
        # Check if admin already exists
        from sqlalchemy import select
        from app.database.models_user import User
        
        existing_admin = db.execute(
            select(User).where(User.username == 'admin')
        ).scalar_one_or_none()
        
        if existing_admin:
            logger.info("Admin user already exists")
            return
        
        # Create admin user
        admin = auth_service.create_user(
            username='admin',
            password='admin123',  # CHANGE THIS IN PRODUCTION!
            email='admin@fortune-trading.local',
            is_superuser=True
        )
        
        # Generate API key
        api_key = auth_service.generate_api_key(admin.id)
        
        logger.info(f"✅ Created admin user (id={admin.id})")
        logger.warning("⚠️  IMPORTANT: Default admin password is 'admin123' - CHANGE THIS IMMEDIATELY!")
        logger.info(f"📝 Admin API Key: {api_key}")
        logger.warning("⚠️  Save this API key - it will not be shown again!")
        
        db.close()
        
    except Exception as e:
        logger.error(f"❌ Failed to create admin user: {e}")

if __name__ == "__main__":
    logger.info("Starting database migration...")
    
    if create_users_tables():
        logger.info("\nCreating default admin user...")
        create_default_admin()
    else:
        logger.error("Migration failed, skipping admin user creation")
