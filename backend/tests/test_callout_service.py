import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from collections import deque

from app.services.callout_service import CalloutService
from app.services.alert_service import AlertService
from app.core.trade_intent import TradeIntent, DirectionalBias, AnalysisQuality

@pytest.fixture
def mock_alert_service():
    service = AsyncMock(spec=AlertService)
    return service

@pytest.fixture
def callout_service(mock_alert_service):
    return CalloutService(mock_alert_service)

def create_intent(symbol="RELIANCE", score=50.0):
    return TradeIntent(
        symbol=symbol,
        analysis_timestamp=datetime.now(),
        directional_bias=DirectionalBias.BULLISH,
        conviction_score=score,
        is_execution_ready=False,
        is_analysis_valid=True,
        # Missing fields
        pillar_contributions=[],
        reasoning_narrative="Test intent",
        quality=AnalysisQuality(
            total_pillars=6, 
            active_pillars=6, 
            placeholder_pillars=0, 
            failed_pillars=[],
            data_age_seconds=0
        )
    )

@pytest.mark.asyncio
async def test_callout_positive_drift(callout_service, mock_alert_service):
    symbol = "RELIANCE"
    
    # 1. Initial State (Low Score) - 4 mins ago (within window)
    old_time = datetime.now() - timedelta(minutes=4)
    callout_service.history[symbol] = deque([(old_time, 40.0)])
    
    # 2. Current State (High Score) - Now
    intent = create_intent(symbol, score=60.0) # +20 drift
    
    await callout_service.process_intent(intent)
    
    # Verify Alert
    mock_alert_service.emit.assert_called_once()
    args, kwargs = mock_alert_service.emit.call_args
    assert kwargs['alert_type'] == "CALLOUT_ACCELERATION"
    assert kwargs['symbol'] == symbol
    assert "conviction surging" in kwargs['message']

@pytest.mark.asyncio
async def test_callout_negative_drift(callout_service, mock_alert_service):
    symbol = "INFY"
    
    # 1. Initial State (High Score) - 4 mins ago
    old_time = datetime.now() - timedelta(minutes=4)
    callout_service.history[symbol] = deque([(old_time, 80.0)])
    
    # 2. Current State (Low Score)
    intent = create_intent(symbol, score=60.0) # -20 drift
    
    await callout_service.process_intent(intent)
    
    mock_alert_service.emit.assert_called_once()
    args, kwargs = mock_alert_service.emit.call_args
    assert kwargs['alert_type'] == "CALLOUT_DETERIORATION"

@pytest.mark.asyncio
async def test_callout_no_drift_noise(callout_service, mock_alert_service):
    symbol = "TCS"
    
    # Small change
    old_time = datetime.now() - timedelta(minutes=5)
    callout_service.history[symbol] = deque([(old_time, 50.0)])
    
    intent = create_intent(symbol, score=55.0) # +5 drift (below threshold)
    
    await callout_service.process_intent(intent)
    
    mock_alert_service.emit.assert_not_called()

@pytest.mark.asyncio
async def test_callout_pruning(callout_service):
    symbol = "WIPRO"
    
    # Add very old entry
    very_old_time = datetime.now() - timedelta(minutes=10)
    callout_service.history[symbol] = deque([(very_old_time, 50.0)])
    
    # Process new intent
    intent = create_intent(symbol, score=50.0)
    await callout_service.process_intent(intent)
    
    # Check that old entry was removed
    history = callout_service.history[symbol]
    assert len(history) == 1
    assert history[0][0] > very_old_time # Should utilize the new timestamp
