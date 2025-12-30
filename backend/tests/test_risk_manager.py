import pytest
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.risk_manager import RiskManager
from app.brokers.base_adapter import Order
from app.database.models_monitoring import PnLSnapshot, TradePerformance

@pytest.fixture
def risk_manager():
    return RiskManager()

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

@pytest.mark.asyncio
async def test_risk_manager_kill_switch(risk_manager, mock_db):
    order = Order(symbol="RELIANCE", exchange="NSE", quantity=100, transaction_type="BUY", order_type="MARKET")
    
    with patch("app.services.risk_manager.redis_client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = "active"
        
        result = await risk_manager.validate_order(order, mock_db, user_id=1)
        
        assert result["allowed"] is False
        assert "GLOBAL_KILL_SWITCH_ACTIVE" in result["blocked_reasons"]

@pytest.mark.asyncio
async def test_risk_manager_position_size(risk_manager, mock_db):
    # Limit is 5000
    order = Order(symbol="RELIANCE", exchange="NSE", quantity=6000, transaction_type="BUY", order_type="MARKET")
    
    with patch("app.services.risk_manager.redis_client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        # We need to mock _check_daily_loss and _check_order_count to pass
        risk_manager._check_daily_loss = AsyncMock(return_value={"check": "daily_loss", "passed": True})
        risk_manager._check_order_count = AsyncMock(return_value={"check": "order_count", "passed": True})
        
        result = await risk_manager.validate_order(order, mock_db, user_id=1)
        
        assert result["allowed"] is False
        assert any("exceeds hard limit" in r for r in result["blocked_reasons"])

@pytest.mark.asyncio
async def test_risk_manager_daily_loss(risk_manager, mock_db):
    order = Order(symbol="RELIANCE", exchange="NSE", quantity=100, transaction_type="BUY", order_type="MARKET")
    
    with patch("app.services.risk_manager.redis_client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        # Mock daily loss breach
        # Limit is -50000
        mock_snapshot = PnLSnapshot(day_pnl=-60000.0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_snapshot
        mock_db.execute.return_value = mock_result
        
        risk_manager._check_order_count = AsyncMock(return_value={"check": "order_count", "passed": True})
        
        result = await risk_manager.validate_order(order, mock_db, user_id=1)
        
        assert result["allowed"] is False
        assert any("Daily loss" in r for r in result["blocked_reasons"])

@pytest.mark.asyncio
async def test_risk_manager_order_count(risk_manager, mock_db):
    order = Order(symbol="RELIANCE", exchange="NSE", quantity=100, transaction_type="BUY", order_type="MARKET")
    
    with patch("app.services.risk_manager.redis_client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        # Mock order count breach
        # Limit is 100
        mock_result = MagicMock()
        mock_result.scalar.return_value = 150
        mock_db.execute.return_value = mock_result
        
        risk_manager._check_daily_loss = AsyncMock(return_value={"check": "daily_loss", "passed": True})
        
        result = await risk_manager.validate_order(order, mock_db, user_id=1)
        
        assert result["allowed"] is False
        assert any("Daily trade count" in r for r in result["blocked_reasons"])
