import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.openalgo_bridge import OpenAlgoServiceBridge
from app.services.execution_service import ExecutionService
from app.core.config import settings

@pytest.mark.asyncio
async def test_bridge_get_execution_mode():
    with patch("httpx.AsyncClient.post") as mock_post:
        # Mock Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": {"mode": True}} # True = Analyze
        mock_post.return_value = mock_response

        mode = await OpenAlgoServiceBridge.get_execution_mode()
        assert mode == "DRY_RUN" # Analyze mode = DRY_RUN

        # Test LIVE case
        mock_response.json.return_value = {"status": "success", "data": {"mode": False}} # False = Live
        mode = await OpenAlgoServiceBridge.get_execution_mode()
        assert mode == "LIVE"

@pytest.mark.asyncio
async def test_bridge_get_open_position():
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": {"quantity": 50}}
        mock_post.return_value = mock_response

        qty = await OpenAlgoServiceBridge.get_open_position("RELIANCE")
        assert qty == 50
        
        # Verify payload
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["symbol"] == "RELIANCE"
        assert kwargs["json"]["strategy"] == "QUAD_STRAT"

@pytest.mark.asyncio
async def test_bridge_place_smart_order():
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "orderid": "12345"}
        mock_post.return_value = mock_response

        res = await OpenAlgoServiceBridge.place_smart_order({"symbol": "TCS", "quantity": 10})
        assert res["status"] == "success"
        assert res["orderid"] == "12345"

@pytest.mark.asyncio
async def test_execution_service_flow():
    # Mock dependencies
    mock_db = AsyncMock()
    mock_snapshot = MagicMock()
    mock_snapshot.ltp = 1000.0
    mock_decision = MagicMock()
    mock_decision.decision_id = "DEC_1"
    mock_decision.valid_till = datetime.max
    mock_decision.decision_ltp = 1000.0

    service = ExecutionService()
    
    # Mock internal components
    service.risk_manager.validate_order = AsyncMock(return_value={"allowed": True})
    service.reasoning.can_execute_trade = AsyncMock(return_value={
        "is_execution_ready": True, 
        "execution_mode": "LIVE",
        "openalgo_mode": "LIVE", # Bridge checks this
        "block_reason": None
    })
    service.alerts.emit = AsyncMock()
    service._log_execution = MagicMock() # Mock the logger helper

    # Mock Bridge calls specifically
    with patch("app.core.openalgo_bridge.OpenAlgoServiceBridge.get_open_position", new_callable=AsyncMock) as mock_get_pos, \
         patch("app.core.openalgo_bridge.OpenAlgoServiceBridge.place_smart_order", new_callable=AsyncMock) as mock_place:
        
        # Scenario: Long Entry. Current Pos = 0. Buy 50.
        mock_get_pos.return_value = 0
        mock_place.return_value = {"status": "success", "orderid": "ORD_1"}

        order_payload = {"action": "BUY", "quantity": 50, "exchange": "NSE"}
        
        result = await service.execute_order(
            symbol="INFY",
            order_payload=order_payload,
            snapshot=mock_snapshot,
            db=mock_db,
            user_id=1,
            decision=mock_decision
        )

        assert result["status"] == "SUCCESS"
        assert result["order_id"] == "ORD_1"
        
        # Verify Smart Order Payload calculation
        # Target should be 0 + 50 = 50
        call_args = mock_place.call_args[0][0]
        assert call_args["position_size"] == 50
        assert call_args["quantity"] == 50
        assert call_args["action"] == "BUY"

        # Scenario: Short Entry. Current Pos = 50. Sell 100 (Flip to -50).
        mock_get_pos.return_value = 50
        
        order_payload = {"action": "SELL", "quantity": 100, "exchange": "NSE"}
        result = await service.execute_order(
            symbol="INFY",
            order_payload=order_payload,
            snapshot=mock_snapshot,
            db=mock_db,
            user_id=1,
            decision=mock_decision
        )
        
        # Target should be 50 - 100 = -50
        call_args = mock_place.call_args[0][0]
        assert call_args["position_size"] == -50
        assert call_args["quantity"] == 100
        assert call_args["action"] == "SELL"


