# backend/tests/test_execution_safety.py

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from app.services.execution_service import ExecutionService
from app.core.config import settings
from app.core.openalgo_bridge import FeedState
from app.core.trade_decision import TradeDecision

@pytest.fixture
def anyio_backend():
    return "asyncio"

class MockSnapshot:
    def __init__(self, ltp=100.0, ltp_source="redis_ws", ltp_age_ms=100):
        self.ltp = ltp
        self.ltp_source = ltp_source
        self.ltp_age_ms = ltp_age_ms

@pytest.fixture
def execution_service():
    # Use in-memory DB for tests
    svc = ExecutionService(db_path=":memory:")
    # Add company to satisfy Foreign Key constraint
    svc.db.add_company("NSE:RELIANCE", "Reliance Industries")
    return svc

@pytest.fixture
def trade_decision_fixture():
    return TradeDecision.create(
        symbol="NSE:RELIANCE",
        signal="BUY",
        confidence=80.0,
        ltp=100.0
    )

@pytest.mark.anyio
async def test_execution_blocked_when_disabled(execution_service):
    # Setting can be patched because ReasoningService reads it inside the method
    with patch("app.core.config.settings.EXECUTION_ENABLED", False):
        snapshot = MockSnapshot()
        payload = {"action": "BUY", "quantity": 1}
        result = await execution_service.execute_order("NSE:RELIANCE", payload, snapshot)
        
        assert result["status"] == "BLOCKED"
        assert result["block_reason"] == "EXECUTION_DISABLED"

@pytest.mark.anyio
async def test_execution_blocked_when_feed_degraded(execution_service):
    with patch("app.core.config.settings.EXECUTION_ENABLED", True):
        # We need to patch the global instance used in ReasoningService
        with patch("app.core.openalgo_bridge.openalgo_client.get_status") as mock_status:
            mock_status.return_value = {
                "feed_state": "DEGRADED", 
                "active_symbols": ["NSE:RELIANCE"],
                "connected": True
            }
            # Also patch the enum-based feed_state which is used in the response dict
            with patch("app.core.openalgo_bridge.openalgo_client.feed_state") as mock_fs:
                mock_fs.value = "DEGRADED"
                
                snapshot = MockSnapshot()
                payload = {"action": "BUY", "quantity": 1}
                result = await execution_service.execute_order("NSE:RELIANCE", payload, snapshot)
                
                assert result["status"] == "BLOCKED"
                assert result["block_reason"] == "FEED_DEGRADED"

@pytest.mark.anyio
async def test_dry_run_mode_success(execution_service, trade_decision_fixture):
    with patch("app.core.config.settings.EXECUTION_ENABLED", True):
        with patch("app.core.config.settings.EXECUTION_MODE", "DRY_RUN"):
            with patch("app.core.openalgo_bridge.openalgo_client.get_status") as mock_status:
                mock_status.return_value = {
                    "feed_state": "HEALTHY", 
                    "active_symbols": ["NSE:RELIANCE"],
                    "connected": True
                }
                with patch("app.core.openalgo_bridge.openalgo_client.feed_state") as mock_fs:
                    mock_fs.value = "HEALTHY"
                    
                    snapshot = MockSnapshot()
                    payload = {"action": "BUY", "quantity": 1}
                    
                    with patch.object(execution_service, "_place_openalgo_order") as mock_place:
                        result = await execution_service.execute_order("NSE:RELIANCE", payload, snapshot, decision=trade_decision_fixture)
                        
                        assert result["status"] == "DRY_RUN_EXECUTION"
                        assert "order_id" in result
                        assert result["order_id"].startswith("DRY_")
                        mock_place.assert_not_called()

@pytest.mark.anyio
async def test_stale_ltp_blocking(execution_service):
    with patch("app.core.config.settings.EXECUTION_ENABLED", True):
        with patch("app.core.openalgo_bridge.openalgo_client.get_status") as mock_status:
            mock_status.return_value = {
                "feed_state": "HEALTHY", 
                "active_symbols": ["NSE:RELIANCE"],
                "connected": True
            }
            snapshot = MockSnapshot(ltp_age_ms=6000)
            payload = {"action": "BUY", "quantity": 1}
            result = await execution_service.execute_order("NSE:RELIANCE", payload, snapshot)
            
            assert result["status"] == "BLOCKED"
            assert result["block_reason"] == "STALE_LTP"

@pytest.mark.anyio
async def test_live_mode_calls_place_order(execution_service, trade_decision_fixture):
    with patch("app.core.config.settings.EXECUTION_ENABLED", True):
        with patch("app.core.config.settings.EXECUTION_MODE", "LIVE"):
            with patch("app.core.openalgo_bridge.openalgo_client.get_status") as mock_status:
                mock_status.return_value = {
                    "feed_state": "HEALTHY", 
                    "active_symbols": ["NSE:RELIANCE"],
                    "connected": True
                }
                with patch("app.core.openalgo_bridge.openalgo_client.feed_state") as mock_fs:
                    mock_fs.value = "HEALTHY"
                    
                    snapshot = MockSnapshot()
                    payload = {"action": "BUY", "quantity": 1}
                    
                    with patch.object(execution_service, "_place_openalgo_order") as mock_place:
                        mock_place.return_value = "ORD_123456"
                        
                        result = await execution_service.execute_order("NSE:RELIANCE", payload, snapshot, decision=trade_decision_fixture)
                        
                        assert result["status"] == "LIVE_SUCCESS"
                        assert result["order_id"] == "ORD_123456"
                        mock_place.assert_called_once()

@pytest.mark.anyio
async def test_drift_blocking(execution_service, trade_decision_fixture):
    with patch("app.core.config.settings.EXECUTION_ENABLED", True):
        with patch("app.core.openalgo_bridge.openalgo_client.get_status") as mock_status:
            mock_status.return_value = {
                "feed_state": "HEALTHY", 
                "active_symbols": ["NSE:RELIANCE"],
                "connected": True
            }
            # Decision LTP is 100. Snapshot LTP is 101 (100 bps drift > 10 bps limit)
            snapshot = MockSnapshot(ltp=101.0)
            payload = {"action": "BUY", "quantity": 1}
            result = await execution_service.execute_order("NSE:RELIANCE", payload, snapshot, decision=trade_decision_fixture)
            
            assert result["status"] == "BLOCKED"
            assert result["block_reason"] == "EXCESSIVE_DRIFT"

@pytest.mark.anyio
async def test_guardrail_blocking(execution_service, trade_decision_fixture):
    with patch("app.core.config.settings.EXECUTION_ENABLED", True):
        with patch("app.core.config.settings.EXECUTION_MODE", "LIVE"):
            with patch("app.core.openalgo_bridge.openalgo_client.get_status") as mock_status:
                mock_status.return_value = {
                    "feed_state": "HEALTHY", 
                    "active_symbols": ["NSE:RELIANCE"],
                    "connected": True
                }
                # Quantity 101 > 100 limit
                snapshot = MockSnapshot()
                payload = {"action": "BUY", "quantity": 101}
                result = await execution_service.execute_order("NSE:RELIANCE", payload, snapshot, decision=trade_decision_fixture)
                
                assert result["status"] == "BLOCKED"
                assert "MAX_QUANTITY_EXCEEDED" in result["block_reason"]
