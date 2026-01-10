"""
Tests for AnomalyDetector Service
"""

import pytest
from datetime import datetime, timedelta

from app.services.anomaly_detector import AnomalyDetector, Anomaly
from app.core.trade_intent import TradeIntent, PillarContribution, AnalysisQuality, DirectionalBias


class TestAnomalyDetector:
    """Test suite for AnomalyDetector service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = AnomalyDetector(history_size=50)
    
    def create_intent(self, pillar_scores=None, timestamp=None, **kwargs):
        """Helper to create a TradeIntent with pillar contributions."""
        if timestamp is None:
            timestamp = datetime.now()
        
        if pillar_scores is None:
            pillar_scores = {
                "trend": 70.0,
                "momentum": 65.0,
                "volatility": 60.0,
                "liquidity": 55.0,
                "sentiment": 50.0,
                "regime": 45.0
            }
        
        contributions = [
            PillarContribution(
                name=name,
                score=score,
                bias="BULLISH" if score > 50 else "BEARISH",
                is_placeholder=False,
                weight_applied=0.16
            )
            for name, score in pillar_scores.items()
        ]
        
        return TradeIntent(
            symbol="TEST",
            analysis_timestamp=timestamp,
            directional_bias=DirectionalBias.BULLISH,
            conviction_score=60.0,
            pillar_contributions=contributions,
            reasoning_narrative="Test reasoning",
            quality=AnalysisQuality(
                total_pillars=6,
                active_pillars=6,
                placeholder_pillars=0,
                failed_pillars=[]
            ),
            is_analysis_valid=True,
            is_execution_ready=True,
            **kwargs
        )
    
    def test_sudden_drop_detection(self):
        """Test detection of sudden score drops."""
        now = datetime.now()
        
        # Create history with normal scores
        intent1 = self.create_intent(
            pillar_scores={"trend": 80.0, "momentum": 75.0, "volatility": 70.0, 
                          "liquidity": 65.0, "sentiment": 60.0, "regime": 55.0},
            timestamp=now - timedelta(minutes=3)
        )
        
        # Create intent with sudden drop in trend
        intent2 = self.create_intent(
            pillar_scores={"trend": 45.0, "momentum": 75.0, "volatility": 70.0,  # Trend dropped 35 points
                          "liquidity": 65.0, "sentiment": 60.0, "regime": 55.0},
            timestamp=now
        )
        
        anomalies1 = self.detector.detect_anomalies(intent1, "TEST")
        anomalies2 = self.detector.detect_anomalies(intent2, "TEST")
        
        # Should detect sudden drop
        assert len(anomalies2) > 0
        sudden_drops = [a for a in anomalies2 if a.type == "SUDDEN_DROP"]
        assert len(sudden_drops) > 0
        assert sudden_drops[0].pillar == "trend"
        assert sudden_drops[0].severity == "HIGH"
    
    def test_stuck_pillar_detection(self):
        """Test detection of stuck pillars."""
        now = datetime.now()
        
        # Create 10 intents with same score for momentum pillar
        for i in range(10):
            intent = self.create_intent(
                pillar_scores={"trend": 70.0 + i, "momentum": 50.0, "volatility": 60.0 + i,  # Momentum stuck at 50
                              "liquidity": 55.0, "sentiment": 50.0 + i, "regime": 45.0},
                timestamp=now + timedelta(minutes=i)
            )
            anomalies = self.detector.detect_anomalies(intent, "TEST")
        
        # Last detection should flag stuck pillar
        stuck_anomalies = [a for a in anomalies if a.type == "STUCK_PILLAR"]
        assert len(stuck_anomalies) > 0
        assert stuck_anomalies[0].pillar == "momentum"
        assert stuck_anomalies[0].severity == "MEDIUM"
    
    def test_divergent_pillars_detection(self):
        """Test detection of high pillar divergence."""
        # Create intent with 3 BULLISH and 3 BEARISH pillars
        intent = self.create_intent(
            pillar_scores={
                "trend": 70.0,      # BULLISH
                "momentum": 65.0,   # BULLISH
                "volatility": 60.0, # BULLISH
                "liquidity": 40.0,  # BEARISH
                "sentiment": 35.0,  # BEARISH
                "regime": 30.0      # BEARISH
            }
        )
        
        anomalies = self.detector.detect_anomalies(intent, "TEST")
        
        # Should not detect divergence (need 5+ of each)
        divergent = [a for a in anomalies if a.type == "DIVERGENT_PILLARS"]
        assert len(divergent) == 0
        
        # Now test with more pillars (would need to extend contributions)
        # For now, this test verifies the threshold logic
    
    def test_extreme_volatility_detection(self):
        """Test detection of extreme score volatility."""
        now = datetime.now()
        
        # Create history with highly volatile trend scores
        volatile_scores = [30.0, 80.0, 25.0, 85.0, 20.0, 90.0]
        
        for i, score in enumerate(volatile_scores):
            intent = self.create_intent(
                pillar_scores={"trend": score, "momentum": 60.0, "volatility": 60.0,
                              "liquidity": 55.0, "sentiment": 50.0, "regime": 45.0},
                timestamp=now + timedelta(minutes=i * 10)
            )
            anomalies = self.detector.detect_anomalies(intent, "TEST")
        
        # Should detect extreme volatility
        volatility_anomalies = [a for a in anomalies if a.type == "EXTREME_VOLATILITY"]
        assert len(volatility_anomalies) > 0
        assert volatility_anomalies[0].pillar == "trend"
        assert volatility_anomalies[0].severity == "LOW"
    
    def test_no_anomalies_with_normal_data(self):
        """Test that normal data doesn't trigger false positives."""
        now = datetime.now()
        
        # Create history with normal, gradually changing scores
        for i in range(10):
            intent = self.create_intent(
                pillar_scores={
                    "trend": 70.0 + i * 0.5,
                    "momentum": 65.0 + i * 0.3,
                    "volatility": 60.0 - i * 0.2,
                    "liquidity": 55.0 + i * 0.1,
                    "sentiment": 50.0 + i * 0.1,
                    "regime": 45.0 + i * 0.2
                },
                timestamp=now + timedelta(minutes=i)
            )
            anomalies = self.detector.detect_anomalies(intent, "TEST")
        
        # Should not detect anomalies with gradual changes
        assert len(anomalies) == 0
    
    def test_history_size_limit(self):
        """Test that history is limited to specified size."""
        detector = AnomalyDetector(history_size=10)
        
        # Add 20 intents
        for i in range(20):
            intent = self.create_intent(timestamp=datetime.now() + timedelta(minutes=i))
            detector.detect_anomalies(intent, "TEST")
        
        # History should be limited to 10
        assert len(detector.history) == 10
    
    def test_clear_history(self):
        """Test clearing detection history."""
        # Add some intents
        for i in range(5):
            intent = self.create_intent()
            self.detector.detect_anomalies(intent, "TEST")
        
        assert len(self.detector.history) == 5
        
        # Clear history
        self.detector.clear_history()
        
        assert len(self.detector.history) == 0
        assert len(self.detector.pillar_score_history) == 0
    
    def test_anomaly_dataclass_fields(self):
        """Test that Anomaly dataclass has required fields."""
        anomaly = Anomaly(
            type="TEST_TYPE",
            pillar="test_pillar",
            severity="HIGH",
            description="Test description",
            detected_at=datetime.now(),
            metric_value=42.0
        )
        
        assert anomaly.type == "TEST_TYPE"
        assert anomaly.pillar == "test_pillar"
        assert anomaly.severity == "HIGH"
        assert anomaly.description == "Test description"
        assert anomaly.metric_value == 42.0
    
    def test_multiple_anomaly_types_detected(self):
        """Test that multiple anomaly types can be detected simultaneously."""
        now = datetime.now()
        
        # Create history with stuck pillar
        for i in range(10):
            intent = self.create_intent(
                pillar_scores={"trend": 50.0, "momentum": 60.0, "volatility": 60.0,  # Trend stuck
                              "liquidity": 55.0, "sentiment": 50.0, "regime": 45.0},
                timestamp=now + timedelta(minutes=i)
            )
            self.detector.detect_anomalies(intent, "TEST")
        
        # Now create intent with sudden drop in another pillar
        intent_with_drop = self.create_intent(
            pillar_scores={"trend": 50.0, "momentum": 25.0, "volatility": 60.0,  # Momentum dropped 35 points
                          "liquidity": 55.0, "sentiment": 50.0, "regime": 45.0},
            timestamp=now + timedelta(minutes=11)
        )
        
        anomalies = self.detector.detect_anomalies(intent_with_drop, "TEST")
        
        # Should detect both stuck pillar and sudden drop
        types = {a.type for a in anomalies}
        assert "STUCK_PILLAR" in types
        assert "SUDDEN_DROP" in types

    def test_pillar_history_skip(self):
        """Test that pillars not in history are skipped in stuck detection."""
        intent = self.create_intent(pillar_scores={"new_pillar": 70.0})
        # Call direct internal method to bypass history update and trigger defensive skip
        anomalies = self.detector._detect_stuck_pillars(intent)
        assert len(anomalies) == 0

    def test_divergent_pillars_actual_trigger(self):
        """Test that high pillar divergence is actually triggered."""
        # Create intent with 5 BULLISH and 5 BEARISH pillars to exceed threshold
        contributions = []
        for i in range(5):
            contributions.append(PillarContribution(
                name=f"bull_{i}", score=80.0, bias="BULLISH", is_placeholder=False, weight_applied=0.1
            ))
            contributions.append(PillarContribution(
                name=f"bear_{i}", score=20.0, bias="BEARISH", is_placeholder=False, weight_applied=0.1
            ))
            
        intent = TradeIntent(
            symbol="TEST",
            analysis_timestamp=datetime.now(),
            directional_bias=DirectionalBias.NEUTRAL,
            conviction_score=50.0,
            pillar_contributions=contributions,
            reasoning_narrative="Divergence test",
            quality=AnalysisQuality(total_pillars=10, active_pillars=10, placeholder_pillars=0, failed_pillars=[]),
            is_analysis_valid=True,
            is_execution_ready=False
        )
        
        anomalies = self.detector.detect_anomalies(intent, "TEST")
        divergent = [a for a in anomalies if a.type == "DIVERGENT_PILLARS"]
        assert len(divergent) > 0
        assert divergent[0].severity == "MEDIUM"
