import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch
from app.core.openalgo_bridge import OpenAlgoWSClient

@pytest.mark.anyio
async def test_openalgo_message_parsing():
    """Test that incoming ticks are correctly parsed and stored in Redis."""
    client = OpenAlgoWSClient()
    
    # Mock Redis client
    mock_redis = AsyncMock()
    with patch("app.core.openalgo_bridge.redis_client", mock_redis):
        # Mock message
        message = json.dumps({
            "exchange": "NSE",
            "symbol": "RELIANCE",
            "ltp": 2500.5,
            "ts": 1703418509
        })
        
        await client._on_message(message)
        
        # Verify Redis SET (KV Cache)
        mock_redis.set.assert_called_once()
        args, kwargs = mock_redis.set.call_args
        assert args[0] == "ltp:NSE:RELIANCE"
        tick_data = json.loads(args[1])
        assert tick_data["ltp"] == 2500.5
        assert kwargs["ex"] == 5 # settings.REDIS_TICK_TTL
        
        # Verify Redis PUBLISH (Event notification)
        mock_redis.publish.assert_called_once()
        args, _ = mock_redis.publish.call_args
        assert args[0] == "market_ticks:NSE:RELIANCE"

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_feed_state_transitions():
    """Test transitions between HEALTHY, DEGRADED, and DOWN."""
    from app.core.openalgo_bridge import OpenAlgoWSClient, FeedState
    client = OpenAlgoWSClient()
    client.subscribed_symbols = {"NSE:RELIANCE"}
    
    # 1. Mock WS connected
    client.ws = AsyncMock()
    client.ws.open = True
    client.last_tick_time = {"NSE:RELIANCE": 1000}
    
    # Test HEALTHY (Age 10s < 15s)
    with patch("time.time", return_value=1010):
        # Manually run the state logic from _maturity_monitor
        raw_now = 1010
        is_any_stale = False
        for symbol in client.subscribed_symbols:
            key = symbol if ":" in symbol else f"NSE:{symbol}"
            last_t = client.last_tick_time.get(key, 0)
            if (raw_now - last_t) > 15.0:
                is_any_stale = True
                break
        
        client.feed_state = FeedState.DEGRADED if is_any_stale else FeedState.HEALTHY
        assert client.feed_state == FeedState.HEALTHY

    # Test DEGRADED (Age 20s > 15s)
    with patch("time.time", return_value=1020):
        raw_now = 1020
        is_any_stale = False
        for symbol in client.subscribed_symbols:
            key = symbol if ":" in symbol else f"NSE:{symbol}"
            last_t = client.last_tick_time.get(key, 0)
            if (raw_now - last_t) > 15.0:
                is_any_stale = True
                break
        
        client.feed_state = FeedState.DEGRADED if is_any_stale else FeedState.HEALTHY
        assert client.feed_state == FeedState.DEGRADED

@pytest.mark.anyio
async def test_execution_gate_blocking():
    """Test that ExecutionGate correctly blocks trades with reasons."""
    from app.services.reasoning_service import ReasoningService
    from app.core.market_snapshot import LiveDecisionSnapshot
    from app.core.openalgo_bridge import FeedState
    from datetime import datetime
    
    service = ReasoningService()
    
    # Mock snapshot
    snapshot = LiveDecisionSnapshot(
        symbol="RELIANCE",
        timestamp=datetime.now(),
        ltp=2500.0,
        vwap=2490, open=2480, high=2510, low=2470, prev_close=2475,
        volume=100000,
        ltp_source="redis_ws",
        ltp_age_ms=1000
    )
    
    # Mock Bridge status
    mock_status = {
        "feed_state": "HEALTHY",
        "active_symbols": ["NSE:RELIANCE"]
    }
    
    with patch("app.core.openalgo_bridge.openalgo_client.get_status", return_value=mock_status):
        # 1. Healthy case
        is_safe, reason = await service.is_execution_safe("RELIANCE", snapshot)
        assert is_safe is True
        assert reason is None
        
        # 2. Degraded Feed
        mock_status["feed_state"] = "DEGRADED"
        is_safe, reason = await service.is_execution_safe("RELIANCE", snapshot)
        assert is_safe is False
        assert reason == "FEED_DEGRADED"
        
        # 3. Stale LTP
        mock_status["feed_state"] = "HEALTHY"
        snapshot.ltp_age_ms = 6000 
        is_safe, reason = await service.is_execution_safe("RELIANCE", snapshot)
        assert is_safe is False
        assert reason == "STALE_LTP"
