
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.reasoning_service import ReasoningService
from app.core.trade_intent import TradeIntent, DirectionalBias, AnalysisQuality
from app.core.market_snapshot import LiveDecisionSnapshot, SessionContext
from datetime import datetime

@pytest.fixture
def mock_engine():
    engine = Mock()
    intent = TradeIntent(
        symbol="TEST",
        analysis_timestamp=datetime.now(),
        directional_bias=DirectionalBias.BULLISH,
        conviction_score=80.0,
        is_execution_ready=True,
        is_analysis_valid=True,
        pillar_contributions=[],
        reasoning_narrative="Test",
        quality=AnalysisQuality(total_pillars=6, active_pillars=6, placeholder_pillars=0, failed_pillars=[]),
        degradation_warnings=[]
    )
    engine.analyze.return_value = intent
    return engine

@pytest.fixture
def mock_snapshot_builder():
    builder = Mock()
    builder.build_snapshot = AsyncMock(return_value=LiveDecisionSnapshot(
        symbol="TEST",
        ltp=100.0,
        timestamp=None,
        prev_close=99.0,
        open=99.0,
        high=101.0,
        low=99.0,
        vwap=100.0,
        ltp_source="redis_ws",
        ltp_age_ms=100,
        bid_price=99.9,
        ask_price=100.1
    ))
    builder.build_session_context = AsyncMock(return_value=SessionContext(
        timestamp=None,
        market_regime="BULLISH",
        vix_level=12.0
    ))
    return builder

@pytest.fixture
def mock_validator():
    validator = Mock()
    result = Mock()
    result.is_valid = True
    result.warnings = []
    validator.validate_indicators = AsyncMock(return_value=result)
    return validator

@pytest.mark.asyncio
async def test_analyze_symbol_integrates_gate(mock_engine, mock_snapshot_builder, mock_validator):
    """
    Verify that analyze_symbol calls the Gate with feed health.
    """
    service = ReasoningService()
    service.engine = mock_engine
    service.snapshot_builder = mock_snapshot_builder
    service.validator = mock_validator
    # Mock operational safety check to pass
    service.is_execution_safe = AsyncMock(return_value=(True, None))
    
    # Mock FeedHealthMonitor
    with patch("app.services.feed_health_monitor.feed_health_monitor") as mock_health_monitor:
        mock_health_monitor.check_health = AsyncMock(return_value={"status": "HEALTHY"})
        
        # Mock Gate
        with patch("app.services.data_integrity_gate.StrictDataIntegrityGate") as mock_gate:
            mock_gate.apply_gate.return_value = mock_engine.analyze.return_value
            
            await service.analyze_symbol("TEST")
            
            # Verify Gate was called
            args, kwargs = mock_gate.apply_gate.call_args
            assert kwargs['feed_health'] == {"status": "HEALTHY"}
            assert kwargs['validation_result'] is not None

@pytest.mark.asyncio
async def test_analyze_symbol_propagates_gate_blocking(mock_engine, mock_snapshot_builder, mock_validator):
    """
    Verify that if Gate blocks, the result reflects it.
    """
    service = ReasoningService()
    service.engine = mock_engine
    service.snapshot_builder = mock_snapshot_builder
    service.validator = mock_validator
    service.is_execution_safe = AsyncMock(return_value=(True, None))
    
    blocked_intent = mock_engine.analyze.return_value
    blocked_intent.is_execution_ready = False
    blocked_intent.execution_block_reason = "BLOCKED_BY_TEST"
    
    with patch("app.services.feed_health_monitor.feed_health_monitor") as mock_health_monitor, \
         patch("app.services.data_integrity_gate.StrictDataIntegrityGate") as mock_gate:
        
        mock_health_monitor.check_health = AsyncMock(return_value={"status": "HEALTHY"})
        mock_gate.apply_gate.return_value = blocked_intent
        
        result = await service.analyze_symbol("TEST")
        
        assert result['is_execution_ready'] is False
        assert result.get('execution_block_reason') == "BLOCKED_BY_TEST"
