# tests/test_quad_v1_1_integration.py

"""
QUAD v1.1 Integration Tests

Tests the complete v1.1 implementation including:
- TradeIntent v1.1 schema extensions
- Decision history storage and retrieval
- Conviction timeline analysis
- Pillar drift measurement
- API endpoints
"""

import pytest
from datetime import datetime, timedelta
from app.core.trade_intent import TradeIntent, DirectionalBias, PillarContribution, AnalysisQuality
from app.core.decision_history import DecisionHistory, DecisionHistoryEntry
from app.core.conviction_timeline import ConvictionTimeline
from app.core.pillar_drift import PillarDriftMeasurement
from app.services.decision_history_service import DecisionHistoryService


class TestTradeIntentV11:
    """Test TradeIntent v1.1 schema extensions."""
    
    def test_analysis_quality_v11_fields(self):
        """Test that AnalysisQuality supports v1.1 fields."""
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
        
        assert quality.calibration_version == "matrix_2024_q4"
        assert quality.pillar_weights_snapshot["trend"] == 0.30
        assert quality.total_pillars == 6  # v1.0 field still works
    
    def test_trade_intent_v11_contract_version(self):
        """Test that TradeIntent has v1.1 contract version."""
        intent = TradeIntent(
            symbol="RELIANCE",
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
        
        assert intent.contract_version == "1.1.0"
        assert intent.quality.calibration_version == "matrix_2024_q4"
    
    def test_backward_compatibility(self):
        """Test that v1.0 consumers can still use v1.1 TradeIntent."""
        # Create v1.1 TradeIntent
        intent = TradeIntent(
            symbol="RELIANCE",
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
                calibration_version="matrix_2024_q4"  # v1.1 field
            ),
            is_analysis_valid=True,
            is_execution_ready=True,
            degradation_warnings=[]
        )
        
        # v1.0 consumer code (only accesses v1.0 fields)
        assert intent.symbol == "RELIANCE"
        assert intent.directional_bias == DirectionalBias.BULLISH
        assert intent.conviction_score == 75.0
        assert intent.quality.total_pillars == 6
        assert intent.is_execution_ready is True
        
        # This should work without errors even though v1.1 fields exist


class TestDecisionHistory:
    """Test decision history functionality."""
    
    def test_create_history_entry_from_trade_intent(self):
        """Test creating DecisionHistoryEntry from TradeIntent."""
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
        
        entry = DecisionHistoryEntry.from_trade_intent(intent, "test_decision_id")
        
        assert entry.decision_id == "test_decision_id"
        assert entry.symbol == "RELIANCE"
        assert entry.directional_bias == DirectionalBias.BULLISH
        assert entry.conviction_score == 75.0
        assert entry.calibration_version == "matrix_2024_q4"
        assert entry.pillar_count_active == 4
        assert "trend" in entry.pillar_scores
        assert entry.pillar_scores["trend"] == 83.33
    
    def test_decision_history_query_helpers(self):
        """Test DecisionHistory query methods."""
        history = DecisionHistory(symbol="RELIANCE")
        
        # Add multiple entries
        for i in range(5):
            entry = DecisionHistoryEntry(
                decision_id=f"dec_{i}",
                symbol="RELIANCE",
                analysis_timestamp=datetime.now() - timedelta(hours=i),
                directional_bias=DirectionalBias.BULLISH if i % 2 == 0 else DirectionalBias.BEARISH,
                conviction_score=70.0 + i,
                pillar_count_active=4,
                pillar_count_placeholder=2,
                pillar_count_failed=0,
                engine_version="1.1.0",
                contract_version="1.1.0"
            )
            history.add_entry(entry)
        
        # Test get_recent
        recent = history.get_recent(limit=3)
        assert len(recent) == 3
        assert recent[0].decision_id == "dec_0"  # Most recent
        
        # Test bias distribution
        bias_dist = history.get_bias_distribution()
        assert bias_dist["BULLISH"] == 3
        assert bias_dist["BEARISH"] == 2
        
        # Test average conviction
        avg = history.get_average_conviction()
        assert avg == 72.0  # (70 + 71 + 72 + 73 + 74) / 5


class TestConvictionTimeline:
    """Test conviction timeline analysis."""
    
    def test_conviction_volatility(self):
        """Test conviction volatility calculation."""
        timeline = ConvictionTimeline(symbol="RELIANCE")
        
        # Add data points with varying conviction
        for i, score in enumerate([50.0, 60.0, 55.0, 70.0, 65.0]):
            timeline.add_data_point(ConvictionDataPoint(
                timestamp=datetime.now() - timedelta(hours=i),
                conviction_score=score,
                directional_bias="BULLISH",
                active_pillars=4
            ))
        
        volatility = timeline.get_conviction_volatility()
        assert volatility > 0  # Should have some volatility
    
    def test_bias_consistency(self):
        """Test bias consistency calculation."""
        timeline = ConvictionTimeline(symbol="RELIANCE")
        
        # All same bias = 100% consistency
        for i in range(5):
            timeline.add_data_point(ConvictionDataPoint(
                timestamp=datetime.now() - timedelta(hours=i),
                conviction_score=70.0,
                directional_bias="BULLISH",
                active_pillars=4
            ))
        
        consistency = timeline.get_bias_consistency()
        assert consistency == 100.0
        
        # Add one different bias
        timeline.add_data_point(ConvictionDataPoint(
            timestamp=datetime.now() - timedelta(hours=5),
            conviction_score=70.0,
            directional_bias="BEARISH",
            active_pillars=4
        ))
        
        consistency = timeline.get_bias_consistency()
        assert consistency < 100.0  # Should decrease


class TestPillarDrift:
    """Test pillar drift measurement."""
    
    def test_drift_calculation(self):
        """Test drift calculation between two snapshots."""
        from app.core.pillar_drift import PillarScoreSnapshot
        
        prev_snapshot = PillarScoreSnapshot(
            timestamp=datetime.now() - timedelta(hours=1),
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
        
        # Check score deltas
        assert drift.score_deltas["trend"] == pytest.approx(8.33, rel=0.01)
        assert drift.score_deltas["momentum"] == 5.0
        assert drift.score_deltas["sentiment"] == 15.0
        
        # Check bias changes
        assert "momentum" in drift.bias_changes
        assert drift.bias_changes["momentum"] == ("NEUTRAL", "BULLISH")
        
        # Check aggregated metrics
        assert drift.max_drift_pillar == "sentiment"
        assert drift.max_drift_magnitude == 15.0
    
    def test_drift_classification(self):
        """Test drift classification (STABLE/MODERATE/HIGH)."""
        from app.core.pillar_drift import PillarScoreSnapshot
        
        # Small drift = STABLE
        prev = PillarScoreSnapshot(
            timestamp=datetime.now() - timedelta(hours=1),
            scores={"trend": 75.0, "momentum": 60.0},
            biases={"trend": "BULLISH", "momentum": "NEUTRAL"}
        )
        
        curr = PillarScoreSnapshot(
            timestamp=datetime.now(),
            scores={"trend": 77.0, "momentum": 62.0},
            biases={"trend": "BULLISH", "momentum": "NEUTRAL"}
        )
        
        drift = PillarDriftMeasurement(symbol="RELIANCE", previous_snapshot=prev, current_snapshot=curr)
        assert drift.get_drift_classification() == "STABLE"


class TestDecisionHistoryService:
    """Test DecisionHistoryService integration."""
    
    @pytest.fixture
    def service(self, tmp_path):
        """Create temporary DecisionHistoryService."""
        db_path = str(tmp_path / "test_history.db")
        return DecisionHistoryService(db_path)
    
    def test_save_and_retrieve_decision(self, service):
        """Test saving and retrieving a decision."""
        intent = TradeIntent(
            symbol="RELIANCE",
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
        assert decision_id is not None
        
        # Retrieve history
        history = service.get_history("RELIANCE")
        assert history.total_decisions == 1
        assert history.entries[0].decision_id == decision_id
        assert history.entries[0].calibration_version == "matrix_2024_q4"
    
    def test_get_latest_decision(self, service):
        """Test retrieving latest decision."""
        # Save multiple decisions
        for i in range(3):
            intent = TradeIntent(
                symbol="RELIANCE",
                analysis_timestamp=datetime.now() - timedelta(hours=i),
                directional_bias=DirectionalBias.BULLISH,
                conviction_score=70.0 + i,
                pillar_contributions=[],
                reasoning_narrative="Test",
                quality=AnalysisQuality(
                    total_pillars=6,
                    active_pillars=4,
                    placeholder_pillars=2,
                    failed_pillars=[]
                ),
                is_analysis_valid=True,
                is_execution_ready=True,
                degradation_warnings=[]
            )
            service.save_decision(intent)
        
        # Get latest
        latest = service.get_latest_decision("RELIANCE")
        assert latest is not None
        assert latest.conviction_score == 70.0  # Most recent (i=0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
