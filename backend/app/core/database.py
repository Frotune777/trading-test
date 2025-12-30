from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# Declarative Base for all models
Base = declarative_base()

# Async Engine (Primary)
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Synchronous Engine (For legacy DatabaseManager consolidation)
# Convert postgresql+asyncpg:// to postgresql:// and sqlite+aiosqlite:// to sqlite://
sync_uri = settings.SQLALCHEMY_DATABASE_URI.replace("postgresql+asyncpg://", "postgresql://").replace("sqlite+aiosqlite://", "sqlite://")
sync_engine = create_engine(sync_uri, pool_pre_ping=True)
SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

async def get_db():
    async with SessionLocal() as session:
        yield session

def get_db_sync():
    db = SessionLocalSync()
    try:
        yield db
    finally:
        db.close()
