"""
Complete QUAD System Validation - All 6 Pillars Active
Tests that Volatility and Liquidity pillars are fully implemented.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from datetime import datetime
from app.core.market_snapshot import LiveDecisionSnapshot, SessionContext
from app.core.trade_intent import DirectionalBias
from app.reasoning.reasoning_engine import ReasoningEngine
from app.reasoning.pillars.trend_pillar import TrendPillar
from app.reasoning.pillars.momentum_pillar import MomentumPillar
from app.reasoning.pillars.volatility_pillar import VolatilityPillar
from app.reasoning.pillars.liquidity_pillar import LiquidityPillar
from app.reasoning.pillars.sentiment_pillar import SentimentPillar
from app.reasoning.pillars.regime_pillar import RegimePillar

def test_complete_quad_system():
    """Test that all 6 QUAD pillars are implemented and active."""
    
    print("=" * 70)
    print("COMPLETE QUAD SYSTEM VALIDATION - ALL 6 PILLARS")
    print("=" * 70)
    
    # Setup engine
    engine = ReasoningEngine()
    engine.register_pillar('trend', TrendPillar())
    engine.register_pillar('momentum', MomentumPillar())
    engine.register_pillar('volatility', VolatilityPillar())
    engine.register_pillar('liquidity', LiquidityPillar())
    engine.register_pillar('sentiment', SentimentPillar())
    engine.register_pillar('regime', RegimePillar())
    
    # Create comprehensive snapshot with ALL indicators
    snapshot = LiveDecisionSnapshot(
        symbol="RELIANCE",
        timestamp=datetime.now(),
        ltp=2500.0,
        vwap=2495.0,
        open=2480.0,
        high=2510.0,
        low=2475.0,
        prev_close=2490.0,
        volume=1000000,
        # Trend indicators
        sma_50=2450.0,
        sma_200=2400.0,
        # Momentum indicators
        rsi=65.0,
        macd=12.5,
        macd_signal=10.0,
        macd_hist=2.5,
        # Volatility indicators (NEW)
        atr=50.0,              # 50 rupees ATR
        atr_pct=2.0,           # 2% ATR (normal volatility)
        bb_width=6.0,          # 6% BB width (normal)
        bb_upper=2600.0,
        bb_middle=2500.0,
        bb_lower=2400.0,
        # Liquidity indicators (NEW)
        bid_price=2499.0,
        ask_price=2501.0,
        bid_qty=5000,
        ask_qty=4800,
        spread_pct=0.08,       # 0.08% spread (tight)
        adosc=500.0            # Positive accumulation
    )
    
    context = SessionContext(
        timestamp=datetime.now(),
        market_regime="BULLISH",
        vix_level=15.5  # Low VIX
    )
    
    # ========== Test 1: Zero Placeholders ==========
    print("\n✓ Test 1: Verifying NO placeholder pillars...")
    assert len(engine.placeholder_pillars) == 0, f"Should have 0 placeholders, found {len(engine.placeholder_pillars)}"
    print(f"  ✓ Placeholder count: {len(engine.placeholder_pillars)} (Perfect!)")
    
    # ========== Test 2: Run Full Analysis ==========
    print("\n✓ Test 2: Running full 6-pillar analysis...")
    intent = engine.analyze(snapshot, context)
    
    print(f"  Symbol: {intent.symbol}")
    print(f"  Bias: {intent.directional_bias.value}")
    print(f"  Conviction: {intent.conviction_score:.1f}%")
    
    # ========== Test 3: All Pillars Active ==========
    print("\n✓ Test 3: Verifying all 6 pillars contributed...")
    assert len(intent.pillar_contributions) == 6, "Should have 6 pillar contributions"
    
    pillar_names = [c.name for c in intent.pillar_contributions]
    expected = ['trend', 'momentum', 'volatility', 'liquidity', 'sentiment', 'regime']
    assert sorted(pillar_names) == sorted(expected), f"Missing pillars: {set(expected) - set(pillar_names)}"
    print(f"  ✓ All 6 pillars present: {pillar_names}")
    
    # ========== Test 4: No Placeholders in Contributions ==========
    print("\n✓ Test 4: Verifying NO placeholders in contributions...")
    placeholders = [c.name for c in intent.pillar_contributions if c.is_placeholder]
    assert len(placeholders) == 0, f"Found placeholders: {placeholders}"
    print(f"  ✓ Zero placeholder pillars: {len(placeholders)}")
    
    # ========== Test 5: Quality Metadata ==========
    print("\n✓ Test 5: Verifying quality metadata...")
    assert intent.quality.total_pillars == 6
    assert intent.quality.active_pillars == 6, f"Expected 6 active, got {intent.quality.active_pillars}"
    assert intent.quality.placeholder_pillars == 0, f"Expected 0 placeholders, got {intent.quality.placeholder_pillars}"
    print(f"  ✓ Active pillars: {intent.quality.active_pillars}/6")
    print(f"  ✓ Placeholder pillars: {intent.quality.placeholder_pillars}/6")
    
    # ========== Test 6: Execution Readiness ==========
    print("\n✓ Test 6: Verifying execution readiness...")
    assert intent.is_execution_ready == True, "Should be execution ready with 0 placeholders"
    print(f"  ✓ Execution ready: {intent.is_execution_ready}")
    
    # ========== Test 7: No Degradation Warnings ==========
    print("\n✓ Test 7: Checking degradation warnings...")
    placeholder_warnings = [w for w in intent.degradation_warnings if 'placeholder' in w.lower()]
    assert len(placeholder_warnings) == 0, f"Found placeholder warnings: {placeholder_warnings}"
    print(f"  ✓ No placeholder warnings ({len(intent.degradation_warnings)} total warnings)")
    for w in intent.degradation_warnings:
        print(f"    - {w}")
    
    # ========== Test 8: Volatility Pillar Scoring ==========
    print("\n✓ Test 8: Testing Volatility Pillar logic...")
    vol_contrib = [c for c in intent.pillar_contributions if c.name == 'volatility'][0]
    print(f"  Volatility score: {vol_contrib.score:.1f}")
    print(f"  Volatility bias: {vol_contrib.bias}")
    print(f"  Is placeholder: {vol_contrib.is_placeholder}")
    
    # Should NOT be neutral (50.0) since we have ATR and BB data
    assert vol_contrib.score != 50.0, "Volatility should not return neutral with data"
    assert not vol_contrib.is_placeholder, "Volatility should not be placeholder"
    
    # With ATR 2.0% (Normal 1.5-3.0%), BB 6% (Normal 4-8%), VIX 15.5 (Normal 15-20)
    # All three map to score 60 per calibration matrix
    # Composite: (60*0.4) + (60*0.3) + (60*0.3) = 60.0
    assert vol_contrib.score >= 55.0, f"Expected normal vol score ~60, got {vol_contrib.score}"
    
    # ========== Test 9: Liquidity Pillar Scoring ==========
    print("\n✓ Test 9: Testing Liquidity Pillar logic...")
    liq_contrib = [c for c in intent.pillar_contributions if c.name == 'liquidity'][0]
    print(f"  Liquidity score: {liq_contrib.score:.1f}")
    print(f"  Liquidity bias: {liq_contrib.bias}")
    print(f"  Is placeholder: {liq_contrib.is_placeholder}")
    
    # Should NOT be neutral (50.0) since we have spread/depth data
    assert liq_contrib.score != 50.0, "Liquidity should not return neutral with data"
    assert not liq_contrib.is_placeholder, "Liquidity should not be placeholder"
    
    # With tight spread (0.08%) and positive ADOSC, score should be high
    # Spread 0.08% maps to 85 (Very Good 0.05-0.10%), Depth balanced ~80, ADOSC +500 adds +5
    # Composite should be ~70-85
    assert liq_contrib.score > 65.0, f"Expected high score for good liquidity, got {liq_contrib.score}"
    
    # ========== Test 10: Overall System Health ==========
    print("\n✓ Test 10: Overall system health check...")
    print(f"  Contract version: {intent.contract_version}")
    print(f"  Analysis valid: {intent.is_analysis_valid}")
    print(f"  Execution ready: {intent.is_execution_ready}")
    
    assert intent.is_analysis_valid == True
    assert intent.is_execution_ready == True
    assert intent.contract_version == "1.0.0"
    
    print("\n" + "=" * 70)
    print("✅ COMPLETE QUAD SYSTEM VALIDATION PASSED")
    print("=" * 70)
    
    # Final summary
    print("\n📊 FINAL PILLAR BREAKDOWN:")
    for contrib in intent.pillar_contributions:
        status = "✅ ACTIVE" if not contrib.is_placeholder else "⚠️ PLACEHOLDER"
        print(f"  {contrib.name.capitalize():12} {contrib.score:5.1f}/100  {contrib.bias:8}  {status}")
    
    print("\n🎯 SYSTEM STATUS:")
    print(f"  Total Pillars: {intent.quality.total_pillars}")
    print(f"  Active Pillars: {intent.quality.active_pillars} (100%)")
    print(f"  Placeholder Pillars: {intent.quality.placeholder_pillars} (0%)")
    print(f"  Failed Pillars: {len(intent.quality.failed_pillars)}")
    print(f"  Execution Ready: {'✅ YES' if intent.is_execution_ready else '❌ NO'}")
    print(f"  Conviction: {intent.conviction_score:.1f}%")
    
    print("\n" + "=" * 70)
    print("🚀 ALL 6 QUAD PILLARS OPERATIONAL")
    print("🔒 SYSTEM IS PRODUCTION-READY")
    print("=" * 70)

if __name__ == "__main__":
    test_complete_quad_system()
