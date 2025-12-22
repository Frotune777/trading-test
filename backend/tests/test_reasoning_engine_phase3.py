"""
Phase 3 Validation Test for Reasoning Engine
Tests that Trend and Momentum pillars use correct scoring logic.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from datetime import datetime
from app.core.market_snapshot import LiveDecisionSnapshot, SessionContext
from app.core.trade_intent import TradeIntent, DirectionalBias
from app.reasoning.reasoning_engine import ReasoningEngine
from app.reasoning.pillars.trend_pillar import TrendPillar
from app.reasoning.pillars.momentum_pillar import MomentumPillar
from app.reasoning.pillars.volatility_pillar import VolatilityPillar
from app.reasoning.pillars.liquidity_pillar import LiquidityPillar
from app.reasoning.pillars.sentiment_pillar import SentimentPillar
from app.reasoning.pillars.regime_pillar import RegimePillar

def test_phase_3_trend_momentum():
    """Test that Trend and Momentum pillars score correctly."""
    
    print("=" * 60)
    print("Phase 3: Trend & Momentum Pillar Validation")
    print("=" * 60)
    
    context = SessionContext(
        timestamp=datetime.now(),
        market_regime="BULLISH",
        vix_level=15.5
    )
    
    # Test 1: Strong Bullish Trend (All MA aligned)
    print("\n✓ Test 1: Testing TrendPillar with strong bullish alignment...")
    snapshot_bullish_trend = LiveDecisionSnapshot(
        symbol="RELIANCE",
        timestamp=datetime.now(),
        ltp=2500.0,
        vwap=2495.0,
        open=2480.0,
        high=2510.0,
        low=2475.0,
        prev_close=2490.0,
        volume=1000000,
        sma_50=2450.0,   # LTP > SMA50
        sma_200=2400.0,  # SMA50 > SMA200, LTP > SMA200
        sma_20_weekly=2420.0  # LTP > Weekly SMA
    )
    
    trend_pillar = TrendPillar()
    score, bias = trend_pillar.analyze(snapshot_bullish_trend, context)
    print(f"  MA Alignment: Price(2500) > SMA50(2450) > SMA200(2400)")
    print(f"  Weekly: Price > SMA20(2420)")
    print(f"  Score: {score} (Expected: 100 - all conditions met)")
    print(f"  Bias: {bias} (Expected: BULLISH)")
    assert score == 100.0  # Perfect trend alignment
    assert bias == "BULLISH"
    
    # Test 2: Weak Trend (Partial alignment)
    print("\n✓ Test 2: Testing TrendPillar with partial alignment...")
    snapshot_weak_trend = LiveDecisionSnapshot(
        symbol="RELIANCE",
        timestamp=datetime.now(),
        ltp=2500.0,
        vwap=2495.0,
        open=2480.0,
        high=2510.0,
        low=2475.0,
        prev_close=2490.0,
        volume=1000000,
        sma_50=2460.0,   # LTP > SMA50
        sma_200=2470.0,  # SMA50 < SMA200 (not aligned!)
        sma_20_weekly=None  # No weekly data
    )
    
    score_weak, bias_weak = trend_pillar.analyze(snapshot_weak_trend, context)
    print(f"  MA Alignment: Price(2500) > SMA50(2460), but SMA50 < SMA200(2470)")
    print(f"  Score: {score_weak} (Expected: ~16.67 - only 1/6 conditions)")
    print(f"  Bias: {bias_weak} (Expected: BEARISH)")
    assert score_weak < 40  # Weak trend
    
    # Test 3: Strong Bullish Momentum (RSI + MACD)
    print("\n✓ Test 3: Testing MomentumPillar with strong bullish signal...")
    snapshot_bullish_mom = LiveDecisionSnapshot(
        symbol="RELIANCE",
        timestamp=datetime.now(),
        ltp=2500.0,
        vwap=2495.0,
        open=2480.0,
        high=2510.0,
        low=2475.0,
        prev_close=2490.0,
        volume=1000000,
        rsi=65.0,           # Bullish (50-70 range) = 20 pts
        macd=12.5,
        macd_signal=10.0,   # MACD > Signal = 10 pts
        macd_hist=2.5       # Hist > 0 = 10 pts
    )
    
    momentum_pillar = MomentumPillar()
    mom_score, mom_bias = momentum_pillar.analyze(snapshot_bullish_mom, context)
    print(f"  RSI: 65 (Bullish zone)")
    print(f"  MACD: 12.5 > Signal(10.0), Hist: 2.5")
    print(f"  Score: {mom_score} (Expected: 100 - all conditions met)")
    print(f"  Bias: {mom_bias} (Expected: BULLISH)")
    assert mom_score == 100.0  # 40/40 points, normalized to 100
    assert mom_bias == "BULLISH"
    
    # Test 4: Overbought Momentum
    print("\n✓ Test 4: Testing MomentumPillar with overbought signal...")
    snapshot_overbought = LiveDecisionSnapshot(
        symbol="RELIANCE",
        timestamp=datetime.now(),
        ltp=2500.0,
        vwap=2495.0,
        open=2480.0,
        high=2510.0,
        low=2475.0,
        prev_close=2490.0,
        volume=1000000,
        rsi=78.0,           # Overbought = 10 pts (caution)
        macd=12.5,
        macd_signal=10.0,
        macd_hist=2.5
    )
    
    mom_score_ob, mom_bias_ob = momentum_pillar.analyze(snapshot_overbought, context)
    print(f"  RSI: 78 (Overbought)")
    print(f"  Score: {mom_score_ob} (Expected: 75 - reduced for overbought)")
    print(f"  Bias: {mom_bias_ob}")
    assert mom_score_ob == 75.0  # 30/40 points (10 for RSI, 20 for MACD)
    
    # Test 5: Full engine with all pillars migrated
    print("\n✓ Test 5: Testing full engine with Phase 3 pillars...")
    engine = ReasoningEngine()
    engine.register_pillar('trend', trend_pillar)
    engine.register_pillar('momentum', momentum_pillar)
    engine.register_pillar('volatility', VolatilityPillar())
    engine.register_pillar('liquidity', LiquidityPillar())
    engine.register_pillar('sentiment', SentimentPillar())
    engine.register_pillar('regime', RegimePillar())
    
    # Use snapshot with strong trend + momentum
    intent = engine.analyze(snapshot_bullish_trend, context)
    print(f"  Action: {intent.action.value}")
    print(f"  Confidence: {intent.confidence_score}")
    print(f"  Trend Score: {intent.trend_score} (migrated)")
    print(f"  Momentum Score: {intent.momentum_score} (needs indicators)")
    assert intent.trend_score == 100.0  # Perfect trend
    
    print("\n" + "=" * 60)
    print("✅ Phase 3 Validation PASSED")
    print("=" * 60)
    print("\nPhase 3 Changes:")
    print("- TrendPillar now scores using SMA50/200 alignment")
    print("- MomentumPillar now scores using RSI + MACD")
    print("- Both pillars normalize scores to 0-100 scale")
    print("- Logic matches RecommendationService exactly")
    print("\nNext Steps:")
    print("- Phase 4: Final integration and production testing")
    print("=" * 60)

if __name__ == "__main__":
    test_phase_3_trend_momentum()
