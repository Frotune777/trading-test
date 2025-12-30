"""
pytest configuration for Fortune Trading QUAD Platform
"""

# CRITICAL: Add app directory to path BEFORE any imports
import sys
from pathlib import Path

# Add to path immediately
app_path = str(Path(__file__).parent.parent)
if app_path not in sys.path:
    sys.path.insert(0, app_path)

# Avoid network calls during test collection
from unittest.mock import patch, AsyncMock, MagicMock

class AsyncMagicMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMagicMock, self).__call__(*args, **kwargs)

def patch_async_mock():
    return AsyncMock()

# Mock Redis to avoid connection hangs
mock_redis = MagicMock()
mock_redis.get = AsyncMock(return_value=None)
mock_redis.set = AsyncMock(return_value=True)
mock_redis.ping = AsyncMock(return_value=True)

patchers = [
    patch('app.core.redis.redis_client', mock_redis),
    patch('app.core.redis.get_redis_client', return_value=mock_redis),
    patch('app.data_sources.nse_master_data.NSEMasterData.download_symbol_master', return_value=None),
    patch('app.data_sources.nse_master_data.NSEMasterData.get_nse_symbol_master', return_value=None),
    patch('app.services.feed_health_monitor.FeedHealthMonitor.start_monitoring', new_callable=patch_async_mock),
    patch('app.services.feed_health_monitor.FeedHealthMonitor.stop_monitoring', new_callable=patch_async_mock),
    patch('app.core.scheduler_config.SchedulerConfig.start', return_value=None),
    patch('app.core.scheduler_config.SchedulerConfig.stop', return_value=None),
]

for p in patchers:
    p.start()

def pytest_configure(config):
    """
    Pytest hook that runs before collection.
    This ensures the path is set before pytest tries to import test modules.
    """
    app_path = str(Path(__file__).parent.parent)
    if app_path not in sys.path:
        sys.path.insert(0, app_path)

import pytest
import asyncio
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add app directory to path (redundant but ensures it's there)
if app_path not in sys.path:
    sys.path.insert(0, app_path)

# Try to import database Base, but don't fail if not available (for broker tests)
try:
    from app.core.database import Base
    HAS_DATABASE = True
except (ImportError, ModuleNotFoundError):
    Base = None
    HAS_DATABASE = False

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh database engine for each test"""
    if not HAS_DATABASE or Base is None:
        pytest.skip("Database not available for this test")
    
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a fresh database session for each test"""
    if not HAS_DATABASE:
        pytest.skip("Database not available for this test")
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "password": "SecurePassword123!",
        "email": "test@example.com"
    }

@pytest.fixture
def test_order_data():
    """Sample order data for testing"""
    return {
        "symbol": "NSE:RELIANCE",
        "exchange": "NSE",
        "action": "BUY",
        "quantity": 10,
        "price": 2500.00,
        "pricetype": "LIMIT",
        "product": "MIS"
    }

@pytest.fixture
def test_quad_data():
    """Sample QUAD analysis data for testing"""
    return {
        "symbol": "RELIANCE",
        "quality_score": 0.85,
        "urgency_score": 0.70,
        "alignment_score": 0.90,
        "drift_score": 0.15,
        "conviction_score": 0.78
    }
