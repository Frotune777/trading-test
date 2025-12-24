#!/usr/bin/env python3
"""
QUAD v1.1 Implementation Verification Script

Verifies that all v1.1 features are working correctly.
"""

import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, '/app')

from app.core.trade_intent import TradeIntent, DirectionalBias, PillarContribution, AnalysisQuality
from app.core.decision_history import DecisionHistory, DecisionHistoryEntry
from app.core.conviction_timeline import ConvictionTimeline, ConvictionDataPoint
from app.core.pillar_drift import PillarDriftMeasurement, PillarScoreSnapshot
from app.services.decision_history_service import DecisionHistoryService


def test_trade_intent_v11():
    """Test TradeIntent v1.1 schema."""
    print("\n🔍 Testing TradeIntent v1.1 Schema...")
    
    quality = AnalysisQuality(
        total_pillars=6,
        active_pillars=4,
        placeholder_pillars=2,
        failed_pillars=[],
        data_age_seconds=5,
        # v1.1 additions
        calibration_version="matrix_2024_q4",
        pillar_weights_snapshot={"trend": 0.30, "momentum": 0.20}
    )
    
    intent = TradeIntent(
        symbol="RELIANCE",
        analysis_timestamp=datetime.now(),
        directional_bias=DirectionalBias.BULLISH,
        conviction_score=75.0,
        pillar_contributions=[
            PillarContribution(
                name="trend",
                score=83.33,
                bias="BULLISH",
                is_placeholder=False,
                weight_applied=0.30,
                metrics={"sma_50": 2450.0}
            )
        ],
        reasoning_narrative="Test narrative",
        quality=quality,
        is_analysis_valid=True,
        is_execution_ready=True,
        degradation_warnings=[]
    )
    
    assert intent.contract_version == "1.1.0", "Contract version should be 1.1.0"
    assert intent.quality.calibration_version == "matrix_2024_q4", "Calibration version should be set"
    assert intent.quality.pillar_weights_snapshot is not None, "Pillar weights snapshot should be set"
    
    print("✅ TradeIntent v1.1 schema working correctly")
    print(f"   - Contract version: {intent.contract_version}")
    print(f"   - Calibration version: {intent.quality.calibration_version}")
    print(f"   - Pillar weights: {intent.quality.pillar_weights_snapshot}")


def test_decision_history():
    """Test decision history functionality."""
    print("\n🔍 Testing Decision History...")
    
    intent = TradeIntent(
        symbol="RELIANCE",
        analysis_timestamp=datetime.now(),
        directional_bias=DirectionalBias.BULLISH,
        conviction_score=75.0,
        pillar_contributions=[
            PillarContribution(
                name="trend",
                score=83.33,
                bias="BULLISH",
                is_placeholder=False,
                weight_applied=0.30
            )
        ],
        reasoning_narrative="Test",
        quality=AnalysisQuality(
            total_pillars=6,
            active_pillars=4,
            placeholder_pillars=2,
            failed_pillars=[],
            calibration_version="matrix_2024_q4"
        ),
        is_analysis_valid=True,
        is_execution_ready=True,
        degradation_warnings=[]
    )
    
    # Create history entry
    entry = DecisionHistoryEntry.from_trade_intent(intent, "test_decision_id")
    
    assert entry.decision_id == "test_decision_id", "Decision ID should match"
    assert entry.calibration_version == "matrix_2024_q4", "Calibration version should be preserved"
    assert "trend" in entry.pillar_scores, "Pillar scores should be stored"
    
    # Create history collection
    history = DecisionHistory(symbol="RELIANCE")
    history.add_entry(entry)
    
    assert history.total_decisions == 1, "Should have 1 decision"
    assert history.get_average_conviction() == 75.0, "Average conviction should be 75.0"
    
    print("✅ Decision history working correctly")
    print(f"   - Entry created with ID: {entry.decision_id}")
    print(f"   - Pillar scores stored: {list(entry.pillar_scores.keys())}")
    print(f"   - Average conviction: {history.get_average_conviction()}")


def test_conviction_timeline():
    """Test conviction timeline analysis."""
    print("\n🔍 Testing Conviction Timeline...")
    
    timeline = ConvictionTimeline(symbol="RELIANCE")
    
    # Add data points
    for i, score in enumerate([50.0, 60.0, 55.0, 70.0, 65.0]):
        timeline.add_data_point(ConvictionDataPoint(
            timestamp=datetime.now(),
            conviction_score=score,
            directional_bias="BULLISH",
            active_pillars=4
        ))
    
    volatility = timeline.get_conviction_volatility()
    consistency = timeline.get_bias_consistency()
    avg_conviction = timeline.get_average_conviction()
    
    assert volatility > 0, "Volatility should be > 0"
    assert consistency == 100.0, "Consistency should be 100% (all same bias)"
    assert avg_conviction == 60.0, "Average conviction should be 60.0"
    
    print("✅ Conviction timeline working correctly")
    print(f"   - Conviction volatility: {volatility:.2f}")
    print(f"   - Bias consistency: {consistency:.1f}%")
    print(f"   - Average conviction: {avg_conviction:.1f}")


def test_pillar_drift():
    """Test pillar drift measurement."""
    print("\n🔍 Testing Pillar Drift Measurement...")
    
    prev_snapshot = PillarScoreSnapshot(
        timestamp=datetime.now(),
        scores={"trend": 75.0, "momentum": 60.0, "sentiment": 55.0},
        biases={"trend": "BULLISH", "momentum": "NEUTRAL", "sentiment": "NEUTRAL"}
    )
    
    curr_snapshot = PillarScoreSnapshot(
        timestamp=datetime.now(),
        scores={"trend": 83.33, "momentum": 65.0, "sentiment": 70.0},
        biases={"trend": "BULLISH", "momentum": "BULLISH", "sentiment": "BULLISH"}
    )
    
    drift = PillarDriftMeasurement(
        symbol="RELIANCE",
        previous_snapshot=prev_snapshot,
        current_snapshot=curr_snapshot
    )
    
    assert drift.max_drift_pillar == "sentiment", "Max drift should be sentiment"
    assert drift.max_drift_magnitude == 15.0, "Max drift magnitude should be 15.0"
    assert "momentum" in drift.bias_changes, "Momentum bias should have changed"
    
    classification = drift.get_drift_classification()
    summary = drift.get_drift_summary()
    
    print("✅ Pillar drift measurement working correctly")
    print(f"   - Max drift pillar: {drift.max_drift_pillar}")
    print(f"   - Max drift magnitude: {drift.max_drift_magnitude}")
    print(f"   - Drift classification: {classification}")
    print(f"   - Summary: {summary}")


def test_decision_history_service():
    """Test DecisionHistoryService."""
    print("\n🔍 Testing DecisionHistoryService...")
    
    service = DecisionHistoryService()
    
    intent = TradeIntent(
        symbol="TEST_SYMBOL",
        analysis_timestamp=datetime.now(),
        directional_bias=DirectionalBias.BULLISH,
        conviction_score=75.0,
        pillar_contributions=[],
        reasoning_narrative="Test",
        quality=AnalysisQuality(
            total_pillars=6,
            active_pillars=4,
            placeholder_pillars=2,
            failed_pillars=[],
            calibration_version="matrix_2024_q4"
        ),
        is_analysis_valid=True,
        is_execution_ready=True,
        degradation_warnings=[]
    )
    
    # Save decision
    decision_id = service.save_decision(intent)
    
    assert decision_id is not None, "Decision ID should be returned"
    
    # Retrieve history
    history = service.get_history("TEST_SYMBOL", limit=1)
    
    assert history.total_decisions == 1, "Should have 1 decision"
    assert history.entries[0].calibration_version == "matrix_2024_q4", "Calibration version should be preserved"
    
    print("✅ DecisionHistoryService working correctly")
    print(f"   - Decision saved with ID: {decision_id}")
    print(f"   - Retrieved {history.total_decisions} decision(s)")
    print(f"   - Calibration version preserved: {history.entries[0].calibration_version}")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("QUAD v1.1 Implementation Verification")
    print("=" * 60)
    
    try:
        test_trade_intent_v11()
        test_decision_history()
        test_conviction_timeline()
        test_pillar_drift()
        test_decision_history_service()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - QUAD v1.1 Implementation Verified!")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
