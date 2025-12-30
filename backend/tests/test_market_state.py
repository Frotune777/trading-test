import pytest
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.market_state_service import MarketStateService, MarketStateSnapshot
from app.database.models_monitoring import TradePerformance

@pytest.fixture
async def mock_db():
    db = AsyncMock(spec=AsyncSession)
    return db

@pytest.mark.asyncio
async def test_get_market_state_fresh(mock_db):
    # Setup
    service = MarketStateService()
    symbol = "RELIANCE"
    ltp_data = {
        "ltp": 2500.0,
        "prev_close": 2480.0,
        "change": 20.0,
        "change_percent": 0.8,
        "high": 2510.0,
        "low": 2475.0,
        "volume": 1000000,
        "timestamp": time.time()
    }
    
    with patch("app.services.market_state_service.redis_client", new_callable=AsyncMock) as mock_redis:
        mock_redis.get.return_value = json.dumps(ltp_data)
        
        with patch("app.services.market_state_service.feed_health_monitor.check_health", new_callable=AsyncMock) as mock_check_health:
            mock_check_health.return_value = {"status": "HEALTHY"}
            
            # Run
            snapshot = await service.get_market_state(symbol, db=mock_db)
            
            # Assert
            assert snapshot.symbol == symbol
            assert snapshot.ltp == 2500.0
            assert snapshot.is_fresh is True
            assert snapshot.feed_status == "HEALTHY"

@pytest.mark.asyncio
async def test_get_market_state_stale(mock_db):
    # Setup
    service = MarketStateService()
    symbol = "RELIANCE"
    ltp_data = {
        "ltp": 2500.0,
        "timestamp": time.time() - 10 # 10 seconds ago (stale)
    }
    
    with patch("app.services.market_state_service.redis_client", new_callable=AsyncMock) as mock_redis:
        mock_redis.get.return_value = json.dumps(ltp_data)
        
        with patch("app.services.market_state_service.feed_health_monitor.check_health", new_callable=AsyncMock) as mock_check_health:
            mock_check_health.return_value = {"status": "HEALTHY"}
            
            # Run
            snapshot = await service.get_market_state(symbol, db=mock_db)
            
            # Assert
            assert snapshot.is_fresh is False
            assert snapshot.data_freshness_ms >= 10000

@pytest.mark.asyncio
async def test_get_market_state_with_user_data(mock_db):
    # Setup
    service = MarketStateService()
    symbol = "RELIANCE"
    user_id = 1
    
    # Mock redis
    with patch("app.services.market_state_service.redis_client", new_callable=AsyncMock) as mock_redis:
        mock_redis.get.return_value = json.dumps({"ltp": 2500.0, "timestamp": time.time()})
        
        # Mock DB results for active trades
        mock_trade = TradePerformance(
            symbol=symbol,
            quantity=100,
            entry_price=2400.0,
            status="OPEN",
            user_id=user_id
        )
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_trade]
        mock_db.execute.return_value = mock_result
        
        # Run
        snapshot = await service.get_market_state(symbol, user_id=user_id, db=mock_db)
        
        # Assert
        assert snapshot.user_state is not None
        assert snapshot.user_state.active_trades_count == 1
        assert snapshot.user_state.total_quantity == 100
        assert snapshot.user_state.avg_price == 2400.0
