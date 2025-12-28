"""
Unit tests for Angel One WebSocket Client
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
import json

from app.brokers.angelone.angelone_websocket import AngelOneWebSocket
from app.brokers.angelone.angelone_auth import AngelOneAuth


class TestAngelOneWebSocket:
    """Test suite for AngelOneWebSocket"""
    
    @pytest.fixture
    def auth(self):
        """Create mock auth"""
        auth = Mock(spec=AngelOneAuth)
        auth.ensure_authenticated = AsyncMock(return_value=True)
        auth.feed_token = "test_feed_token"
        auth.client_id = "test_client_id"
        return auth
    
    @pytest.fixture
    def ws_client(self, auth):
        """Create WebSocket client instance"""
        return AngelOneWebSocket(
            auth=auth,
            ws_url="wss://smartapisocket.angelone.in/smart-stream"
        )
    
    @pytest.mark.asyncio
    async def test_connect_success(self, ws_client, auth):
        """Test successful WebSocket connection"""
        with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = AsyncMock()
            mock_ws.send = AsyncMock()
            mock_ws.recv = AsyncMock(return_value=json.dumps({
                "type": "connection",
                "status": "success"
            }))
            mock_connect.return_value.__aenter__.return_value = mock_ws
            
            result = await ws_client.connect()
            
            assert result is True
            assert ws_client._connected is True
    
    @pytest.mark.asyncio
    async def test_subscribe_symbols(self, ws_client):
        """Test symbol subscription"""
        ws_client._connected = True
        ws_client._ws = AsyncMock()
        ws_client._ws.send = AsyncMock()
        
        symbols = ["NSE:RELIANCE", "NSE:TCS"]
        result = await ws_client.subscribe(symbols)
        
        assert result is True
        assert "NSE:RELIANCE" in ws_client._subscribed_symbols
        assert "NSE:TCS" in ws_client._subscribed_symbols
    
    @pytest.mark.asyncio
    async def test_unsubscribe_symbols(self, ws_client):
        """Test symbol unsubscription"""
        ws_client._connected = True
        ws_client._ws = AsyncMock()
        ws_client._ws.send = AsyncMock()
        ws_client._subscribed_symbols = {"NSE:RELIANCE", "NSE:TCS"}
        
        result = await ws_client.unsubscribe(["NSE:RELIANCE"])
        
        assert result is True
        assert "NSE:RELIANCE" not in ws_client._subscribed_symbols
        assert "NSE:TCS" in ws_client._subscribed_symbols
    
    @pytest.mark.asyncio
    async def test_message_handler_tick(self, ws_client):
        """Test tick message handling"""
        tick_data = {
            "type": "tick",
            "symbol": "NSE:RELIANCE",
            "ltp": 2550.50,
            "volume": 1000000,
            "timestamp": "2025-12-28T23:59:00"
        }
        
        callback = Mock()
        ws_client.on_tick = callback
        
        await ws_client._handle_message(json.dumps(tick_data))
        
        callback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_heartbeat(self, ws_client):
        """Test heartbeat mechanism"""
        ws_client._connected = True
        ws_client._ws = AsyncMock()
        ws_client._ws.send = AsyncMock()
        
        await ws_client._send_heartbeat()
        
        ws_client._ws.send.assert_called_once()
        call_args = ws_client._ws.send.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "heartbeat"
    
    @pytest.mark.asyncio
    async def test_disconnect(self, ws_client):
        """Test WebSocket disconnection"""
        ws_client._connected = True
        ws_client._ws = AsyncMock()
        ws_client._ws.close = AsyncMock()
        
        await ws_client.disconnect()
        
        assert ws_client._connected is False
        ws_client._ws.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reconnect_on_disconnect(self, ws_client):
        """Test automatic reconnection"""
        ws_client._connected = False
        ws_client._reconnect_attempts = 0
        
        with patch.object(ws_client, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = True
            
            result = await ws_client._reconnect()
            
            assert result is True
            mock_connect.assert_called_once()
    
    def test_symbol_token_mapping(self, ws_client):
        """Test symbol to token mapping"""
        # This would test the symbol token resolution logic
        # Implementation depends on how symbol tokens are managed
        pass
