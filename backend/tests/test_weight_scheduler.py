"""
Tests for WeightScheduler Service
"""

import pytest
from app.services.weight_scheduler import WeightScheduler


class TestWeightScheduler:
    """Test suite for WeightScheduler service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scheduler = WeightScheduler()
    
    def test_bullish_regime_weights(self):
        """Test that BULLISH regime returns correct weights."""
        weights = self.scheduler.get_weights("BULLISH")
        
        assert weights["trend"] == 0.35
        assert weights["momentum"] == 0.25
        assert weights["volatility"] == 0.05
        assert sum(weights.values()) == pytest.approx(1.0, abs=0.001)
    
    def test_bearish_regime_weights(self):
        """Test that BEARISH regime returns correct weights."""
        weights = self.scheduler.get_weights("BEARISH")
        
        assert weights["trend"] == 0.35
        assert weights["volatility"] == 0.20
        assert weights["momentum"] == 0.15
        assert sum(weights.values()) == pytest.approx(1.0, abs=0.001)
    
    def test_volatile_regime_weights(self):
        """Test that VOLATILE regime emphasizes volatility and liquidity."""
        weights = self.scheduler.get_weights("VOLATILE")
        
        assert weights["volatility"] == 0.30
        assert weights["liquidity"] == 0.20
        assert weights["trend"] == 0.15
        assert sum(weights.values()) == pytest.approx(1.0, abs=0.001)
    
    def test_sideways_regime_weights(self):
        """Test that SIDEWAYS regime boosts sentiment."""
        weights = self.scheduler.get_weights("SIDEWAYS")
        
        assert weights["sentiment"] == 0.25
        assert weights["regime"] == 0.20
        assert sum(weights.values()) == pytest.approx(1.0, abs=0.001)
    
    def test_unknown_regime_fallback(self):
        """Test that unknown regime falls back to default weights."""
        weights = self.scheduler.get_weights("UNKNOWN_REGIME")
        
        assert weights["trend"] == 0.30
        assert weights["momentum"] == 0.20
        assert sum(weights.values()) == pytest.approx(1.0, abs=0.001)
    
    def test_low_vix_adjustment(self):
        """Test that low VIX reduces volatility weight, boosts trend."""
        weights = self.scheduler.get_weights("BULLISH", vix_level=12.0)
        
        # Should reduce volatility and boost trend
        assert weights["volatility"] < 0.05  # Less than base BULLISH volatility
        assert weights["trend"] > 0.35  # More than base BULLISH trend
        assert sum(weights.values()) == pytest.approx(1.0, abs=0.001)
    
    def test_high_vix_adjustment(self):
        """Test that high VIX increases volatility weight, reduces trend."""
        weights = self.scheduler.get_weights("BULLISH", vix_level=30.0)
        
        # Should increase volatility and reduce trend
        assert weights["volatility"] > 0.05  # More than base BULLISH volatility
        assert weights["trend"] < 0.35  # Less than base BULLISH trend
        assert sum(weights.values()) == pytest.approx(1.0, abs=0.001)
    
    def test_normal_vix_no_adjustment(self):
        """Test that normal VIX (15-25) doesn't trigger adjustments."""
        weights_no_vix = self.scheduler.get_weights("BULLISH")
        weights_normal_vix = self.scheduler.get_weights("BULLISH", vix_level=18.0)
        
        # Should be identical
        assert weights_no_vix == weights_normal_vix
    
    def test_should_rebalance_on_regime_change(self):
        """Test that rebalancing is triggered on regime change."""
        assert self.scheduler.should_rebalance("BULLISH", "BEARISH") is True
        assert self.scheduler.should_rebalance("VOLATILE", "SIDEWAYS") is True
    
    def test_should_not_rebalance_same_regime(self):
        """Test that rebalancing is not triggered for same regime."""
        assert self.scheduler.should_rebalance("BULLISH", "BULLISH") is False
        assert self.scheduler.should_rebalance("SIDEWAYS", "SIDEWAYS") is False
    
    def test_should_not_rebalance_no_previous(self):
        """Test that rebalancing is not triggered when no previous regime."""
        assert self.scheduler.should_rebalance("BULLISH", None) is False
    
    def test_get_schedule_reason(self):
        """Test schedule reason generation."""
        reason = self.scheduler.get_schedule_reason("BULLISH")
        assert reason == "BULLISH"
        
        reason_low_vix = self.scheduler.get_schedule_reason("BULLISH", vix_level=12.0)
        assert reason_low_vix == "BULLISH_LOW_VIX"
        
        reason_high_vix = self.scheduler.get_schedule_reason("BEARISH", vix_level=30.0)
        assert reason_high_vix == "BEARISH_HIGH_VIX"
    
    def test_weights_sum_to_one(self):
        """Test that all weight matrices sum to 1.0."""
        regimes = ["BULLISH", "BEARISH", "VOLATILE", "SIDEWAYS", "NEUTRAL"]
        
        for regime in regimes:
            weights = self.scheduler.get_weights(regime)
            assert sum(weights.values()) == pytest.approx(1.0, abs=0.001), \
                f"{regime} weights don't sum to 1.0"
    
    def test_disabled_scheduler_returns_default(self):
        """Test that disabled scheduler returns default weights."""
        # Temporarily disable scheduler
        self.scheduler.enabled = False
        
        weights = self.scheduler.get_weights("BULLISH")
        assert weights == self.scheduler.default_weights
        
        # Re-enable
        self.scheduler.enabled = True
