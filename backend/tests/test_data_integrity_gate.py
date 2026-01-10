import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from app.services.data_integrity_gate import StrictDataIntegrityGate
from app.core.market_snapshot import LiveDecisionSnapshot
from app.core.trade_intent import TradeIntent, DirectionalBias, AnalysisQuality

@pytest.fixture
def mock_snapshot():
    return LiveDecisionSnapshot(
        symbol="TEST",
        ltp=100.0,
        timestamp=datetime.now(),
        prev_close=99.0,
        open=99.0,
        high=101.0,
        low=99.0,
        vwap=100.0,
        ltp_source="redis_ws",
        ltp_age_ms=100, # 0.1s age (fresh)
        bid_price=99.9,
        ask_price=100.1
    )

@pytest.fixture
def mock_intent():
    return TradeIntent(
        symbol="TEST",
        analysis_timestamp=datetime.now(),
        directional_bias=DirectionalBias.BULLISH,
        conviction_score=80.0,
        is_execution_ready=True,
        is_analysis_valid=True,
        pillar_contributions=[],
        reasoning_narrative="Test",
        quality=AnalysisQuality(
            total_pillars=6,
            active_pillars=6,
            placeholder_pillars=0, 
            failed_pillars=[]
        ),
        degradation_warnings=[]
    )

def test_gate_allows_healthy_feed(mock_intent, mock_snapshot):
    """
    Validation: Healthy feed, fresh data -> PASS
    """
    is_safe, reason = StrictDataIntegrityGate.evaluate_intent(
        mock_intent, 
        mock_snapshot,
        feed_health={"status": "HEALTHY"}
    )
    assert is_safe is True
    assert reason is None

def test_rule_11_unhealthy_feed_blocks(mock_intent, mock_snapshot):
    """
    Rule #11: If feed health != HEALTHY -> BLOCK
    """
    is_safe, reason = StrictDataIntegrityGate.evaluate_intent(
        mock_intent, 
        mock_snapshot,
        feed_health={"status": "DEGRADED"}
    )
    assert is_safe is False
    assert "RULE_11_UNSAFE_FEED_DEGRADED" in reason

def test_rule_8_stale_data_blocks(mock_intent, mock_snapshot):
    """
    Rule #8: If freshness > 5s -> BLOCK
    """
    mock_snapshot.ltp_age_ms = 6000 # 6s old
    is_safe, reason = StrictDataIntegrityGate.evaluate_intent(mock_intent, mock_snapshot)
    assert is_safe is False
    assert "RULE_8_STALE_DATA" in reason

def test_rule_9_unknown_freshness_blocks(mock_intent, mock_snapshot):
    """
    Rule #9: If freshness unknown -> BLOCK
    """
    mock_snapshot.ltp_age_ms = None
    is_safe, reason = StrictDataIntegrityGate.evaluate_intent(mock_intent, mock_snapshot)
    assert is_safe is False
    assert "RULE_9_STALE_UNKNOWN_FRESHNESS" in reason

def test_rule_6_failed_pillar_blocks(mock_intent, mock_snapshot):
    """
    Rule #6: If pillar failed -> BLOCK
    """
    mock_intent.quality.failed_pillars = ["momentum"]
    is_safe, reason = StrictDataIntegrityGate.evaluate_intent(mock_intent, mock_snapshot)
    assert is_safe is False
    assert "RULE_6_PILLAR_FAILURE" in reason

def test_rule_6_cross_validation_blocks(mock_intent, mock_snapshot):
    """
    Rule #6 (Extended): If cross-validation fails -> BLOCK
    """
    validation_result = Mock()
    validation_result.is_valid = False
    validation_result.warnings = ["RSI Divergence"]
    
    is_safe, reason = StrictDataIntegrityGate.evaluate_intent(
        mock_intent, 
        mock_snapshot,
        validation_result=validation_result
    )
    assert is_safe is False
    assert "RULE_6_DATA_DIVERGENCE" in reason

def test_apply_gate_modifies_intent(mock_intent, mock_snapshot):
    """
    Verify apply_gate updates the intent object correctly.
    """
    mock_snapshot.ltp_age_ms = 6000 # Stale
    
    processed_intent = StrictDataIntegrityGate.apply_gate(mock_intent, mock_snapshot)
    
    assert processed_intent.is_execution_ready is False
    assert "RULE_8_STALE_DATA" in processed_intent.execution_block_reason
    assert len(processed_intent.degradation_warnings) > 0
