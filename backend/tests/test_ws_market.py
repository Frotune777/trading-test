import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_websocket_broadcast():
    """Test that Redis ticks are broadcasted to connected WebSocket clients."""
    with TestClient(app) as client:
        # Mock Redis publish message
        mock_tick = {
            "ltp": 2505.5,
            "ts": 1703418510,
            "source": "openalgo_ws"
        }
        
        # Use a context manager to handle the websocket connection
        with client.websocket_connect("/api/v1/ws") as websocket:
            # Send subscription
            websocket.send_json({
                "action": "subscribe",
                "symbols": ["RELIANCE"]
            })
            
            # Simulate Redis broadcast
            from app.api.v1.endpoints.ws_market import manager
            await manager.broadcast_tick("RELIANCE", mock_tick)
            
            # Receive message
            data = websocket.receive_json()
            assert data["type"] == "tick"
            assert data["symbol"] == "RELIANCE"
            assert data["data"]["ltp"] == 2505.5

@pytest.mark.anyio
async def test_websocket_ping_pong():
    """Test the WebSocket heart-beat."""
    with TestClient(app) as client:
        with client.websocket_connect("/api/v1/ws") as websocket:
            websocket.send_json({"action": "ping"})
            data = websocket.receive_json()
            assert data["type"] == "pong"
