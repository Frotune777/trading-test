import pytest
import json
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.openalgo_bridge import OpenAlgoWSClient
from app.database.models_historical import MarketTick, HistoricalOHLC

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_tick_buffering_and_payload():
    """Verify that ticks are added to buffer and payload contains volume/oi."""
    client = OpenAlgoWSClient()
    
    # Mock Redis
    mock_redis = AsyncMock()
    with patch("app.core.openalgo_bridge.redis_client", mock_redis):
        message = json.dumps({
            "exchange": "NSE",
            "symbol": "RELIANCE",
            "ltp": 2500.5,
            "volume": 1000,
            "oi": 500,
            "ts": 1703418509
        })
        
        await client._on_message(message)
        
        # Check buffer
        assert client.tick_buffer.qsize() == 1
        tick = await client.tick_buffer.get()
        assert tick["symbol"] == "RELIANCE"
        assert tick["volume"] == 1000
        assert tick["oi"] == 500
        
        # Check Redis payload
        args, _ = mock_redis.set.call_args
        payload = json.loads(args[1])
        assert payload["volume"] == 1000
        assert payload["oi"] == 500

@pytest.mark.anyio
async def test_tick_flushing_to_db():
    """Verify that buffered ticks are batch-saved to PostgreSQL."""
    client = OpenAlgoWSClient()
    ticks = [
        {"symbol": "RELIANCE", "exchange": "NSE", "ltp": 2500.5, "volume": 1000, "oi": 500, "timestamp": 1703418509},
        {"symbol": "RELIANCE", "exchange": "NSE", "ltp": 2501.0, "volume": 1100, "oi": 500, "timestamp": 1703418510}
    ]
    
    mock_session = AsyncMock()
    with patch("app.core.openalgo_bridge.SessionLocal", return_value=mock_session):
        await client._save_ticks_batch(ticks)
        
        # Verify DB interaction
        mock_session.__aenter__.return_value.add_all.assert_called_once()
        mock_session.__aenter__.return_value.commit.assert_called_once()
        
        added_objs = mock_session.__aenter__.return_value.add_all.call_args[0][0]
        assert len(added_objs) == 2
        assert isinstance(added_objs[0], MarketTick)
        assert added_objs[0].symbol == "RELIANCE"

@pytest.mark.anyio
async def test_deterministic_candle_generation():
    """Verify RealtimeWorker generates candles based on tick timestamps."""
    from app.workers.realtime_worker import realtime_worker as worker_main
    from app.core.openalgo_bridge import openalgo_client
    
    # Mock dependencies
    mock_redis = AsyncMock()
    mock_session = AsyncMock()
    mock_alerts = AsyncMock()
    
    # Setup mock ticks for boundary crossing
    # Tick 1: 10:00:59
    tick1 = json.dumps({"ltp": 100, "volume": 1000, "ts": 1703418059})
    # Tick 2: 10:01:01 (Boundary cross)
    tick2 = json.dumps({"ltp": 105, "volume": 1200, "ts": 1703418061})
    
    # We'll mock redis.get to return tick1 then tick2
    mock_redis.get.side_errors = [tick1, tick2] # Not quite how side_effect works for get
    mock_redis.get.side_effect = [tick1, tick2, None, None, None, Exception("Stop Loop")]
    
    openalgo_client.subscribed_symbols = {"NSE:RELIANCE"}
    
    with patch("app.workers.realtime_worker.redis_client", mock_redis), \
         patch("app.workers.realtime_worker.SessionLocal", return_value=mock_session), \
         patch("app.workers.realtime_worker.AlertService", return_value=mock_alerts):
        
        # This will run the loop until Exception
        try:
            await worker_main()
        except Exception as e:
            if str(e) != "Stop Loop":
                raise e
        
        # Verify candle was saved
        mock_session.__aenter__.return_value.add.assert_called()
        added_candle = mock_session.__aenter__.return_value.add.call_args[0][0]
        assert isinstance(added_candle, HistoricalOHLC)
        assert added_candle.symbol == "RELIANCE"
        assert float(added_candle.open) == 100.0
        assert float(added_candle.close) == 100.0 # First candle close is the last tick of that minute
        assert added_candle.volume == 0 # First candle volume is 0 because we just started
        
        # Note: In the implemented logic, when tick2 (10:01:01) arrives,
        # it closes the 10:00:00 candle.
