"""
Database initialization script
Creates all tables in PostgreSQL database
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.database.models_quad import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    """Initialize database tables"""
    logger.info(f"Connecting to database: {settings.SQLALCHEMY_DATABASE_URI}")
    
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=True
    )
    
    async with engine.begin() as conn:
        logger.info("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    logger.info("✅ Database initialization complete")


if __name__ == "__main__":
    asyncio.run(init_db())
