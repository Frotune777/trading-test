"""
Phase 2 Validation Test for Reasoning Engine
Tests that Regime and Sentiment pillars are wired correctly.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from datetime import datetime
from app.core.market_snapshot import LiveDecisionSnapshot, SessionContext
from app.core.trade_intent import TradeIntent, TradeAction
from app.reasoning.reasoning_engine import ReasoningEngine
from app.reasoning.pillars.trend_pillar import TrendPillar
from app.reasoning.pillars.momentum_pillar import MomentumPillar
from app.reasoning.pillars.volatility_pillar import VolatilityPillar
from app.reasoning.pillars.liquidity_pillar import LiquidityPillar
from app.reasoning.pillars.sentiment_pillar import SentimentPillar
from app.reasoning.pillars.regime_pillar import RegimePillar

def test_phase_2_wiring():
    """Test that Regime and Sentiment pillars use real data."""
    
    print("=" * 60)
    print("Phase 2: Regime & Sentiment Pillar Validation")
    print("=" * 60)
    
    # Test 1: Regime Pillar with Bullish market
    print("\n✓ Test 1: Testing RegimePillar with BULLISH regime...")
    snapshot_neutral = LiveDecisionSnapshot(
        symbol="RELIANCE",
        timestamp=datetime.now(),
        ltp=2500.0,
        vwap=2495.0,
        open=2480.0,
        high=2510.0,
        low=2475.0,
        prev_close=2490.0,
        volume=1000000
    )
    
    context_bullish = SessionContext(
        timestamp=datetime.now(),
        market_regime="BULLISH",
        vix_level=15.5,
        vix_percentile=45.0
    )
    
    regime_pillar = RegimePillar()
    score, bias = regime_pillar.analyze(snapshot_neutral, context_bullish)
    print(f"  Regime: BULLISH, VIX: 15.5")
    print(f"  Score: {score} (Expected: ~90.0)")
    print(f"  Bias: {bias} (Expected: BULLISH)")
    assert bias == "BULLISH"
    assert score > 80  # Should be high for bullish in low VIX
    
    # Test 2: Regime Pillar with high VIX
    print("\n✓ Test 2: Testing RegimePillar with high VIX...")
    context_high_vix = SessionContext(
        timestamp=datetime.now(),
        market_regime="BULLISH",
        vix_level=28.0,  # High volatility
        vix_percentile=85.0
    )
    
    score_high_vix, bias_high_vix = regime_pillar.analyze(snapshot_neutral, context_high_vix)
    print(f"  Regime: BULLISH, VIX: 28.0 (High)")
    print(f"  Score: {score_high_vix} (Expected: <85 due to VIX penalty)")
    print(f"  Bias: {bias_high_vix}")
    assert score_high_vix < score  # High VIX should reduce score
    
    # Test 3: Sentiment Pillar with no derivatives
    print("\n✓ Test 3: Testing SentimentPillar with no derivatives...")
    sentiment_pillar = SentimentPillar()
    score_no_deriv, bias_no_deriv = sentiment_pillar.analyze(snapshot_neutral, context_bullish)
    print(f"  No Greeks/OI data")
    print(f"  Score: {score_no_deriv} (Expected: 50.0 neutral)")
    print(f"  Bias: {bias_no_deriv} (Expected: NEUTRAL)")
    assert score_no_deriv == 50.0
    assert bias_no_deriv == "NEUTRAL"
    
    # Test 4: Sentiment Pillar with bullish derivatives signal
    print("\n✓ Test 4: Testing SentimentPillar with bullish signal...")
    snapshot_bullish_deriv = LiveDecisionSnapshot(
        symbol="RELIANCE",
        timestamp=datetime.now(),
        ltp=2510.0,  # Price up
        vwap=2505.0,
        open=2480.0,
        high=2515.0,
        low=2475.0,
        prev_close=2490.0,  # Price increased
        volume=1000000,
        oi_change=50000,  # OI increased (Long buildup)
        delta=0.65  # Call-heavy
    )
    
    score_bullish, bias_bullish = sentiment_pillar.analyze(snapshot_bullish_deriv, context_bullish)
    print(f"  Price up + OI up + Delta 0.65")
    print(f"  Score: {score_bullish} (Expected: >50)")
    print(f"  Bias: {bias_bullish} (Expected: BULLISH)")
    assert bias_bullish == "BULLISH"
    assert score_bullish > 50  # Should be bullish
    
    # Test 5: Full engine with wired pillars
    print("\n✓ Test 5: Testing full engine with Phase 2 pillars...")
    engine = ReasoningEngine()
    engine.register_pillar('trend', TrendPillar())
    engine.register_pillar('momentum', MomentumPillar())
    engine.register_pillar('volatility', VolatilityPillar())
    engine.register_pillar('liquidity', LiquidityPillar())
    engine.register_pillar('sentiment', sentiment_pillar)
    engine.register_pillar('regime', regime_pillar)
    
    intent = engine.analyze(snapshot_bullish_deriv, context_bullish)
    print(f"  Action: {intent.action.value}")
    print(f"  Confidence: {intent.confidence_score}")
    print(f"  Regime Score: {intent.regime_score} (wired)")
    print(f"  Sentiment Score: {intent.sentiment_score} (wired)")
    assert intent.regime_score > 80  # Bullish regime
    assert intent.sentiment_score > 50  # Bullish derivatives
    
    print("\n" + "=" * 60)
    print("✅ Phase 2 Validation PASSED")
    print("=" * 60)
    print("\nPhase 2 Changes:")
    print("- RegimePillar now uses SessionContext.market_regime")
    print("- RegimePillar adjusts score based on VIX level")
    print("- SentimentPillar analyzes OI Change + Delta + Gamma")
    print("- Both pillars return data-driven scores, not hardcoded")
    print("\nNext Steps:")
    print("- Phase 3: Migrate Trend/Momentum logic from RecommendationService")
    print("=" * 60)

if __name__ == "__main__":
    test_phase_2_wiring()
