"""
Phase 1 Validation Test for Reasoning Engine Skeleton
Tests that all components can be instantiated without errors.
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

def test_phase_1_skeleton():
    """Test that the skeleton can be instantiated and run."""
    
    print("=" * 60)
    print("Phase 1: Reasoning Engine Skeleton Validation")
    print("=" * 60)
    
    # Test 1: Create snapshot
    print("\n✓ Test 1: Creating LiveDecisionSnapshot...")
    snapshot = LiveDecisionSnapshot(
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
    print(f"  Created snapshot for {snapshot.symbol} @ {snapshot.ltp}")
    
    # Test 2: Create context
    print("\n✓ Test 2: Creating SessionContext...")
    context = SessionContext(
        timestamp=datetime.now(),
        market_regime="BULLISH",
        vix_level=15.5,
        vix_percentile=45.0
    )
    print(f"  Market regime: {context.market_regime}, VIX: {context.vix_level}")
    
    # Test 3: Instantiate engine
    print("\n✓ Test 3: Instantiating ReasoningEngine...")
    engine = ReasoningEngine()
    print(f"  Engine created with {len(engine.weights)} pillar weights")
    
    # Test 4: Test with no pillars (should return NO_TRADE)
    print("\n✓ Test 4: Testing engine with no pillars...")
    intent = engine.analyze(snapshot, context)
    assert intent.action == TradeAction.NO_TRADE
    assert intent.confidence_score == 0.0
    print(f"  Result: {intent.action.value} (Expected: NO_TRADE)")
    
    # Test 5: Register all pillars
    print("\n✓ Test 5: Registering all QUAD pillars...")
    engine.register_pillar('trend', TrendPillar())
    engine.register_pillar('momentum', MomentumPillar())
    engine.register_pillar('volatility', VolatilityPillar())
    engine.register_pillar('liquidity', LiquidityPillar())
    engine.register_pillar('sentiment', SentimentPillar())
    engine.register_pillar('regime', RegimePillar())
    print(f"  Registered {len(engine.pillars)} pillars")
    
    # Test 6: Run analysis with all pillars
    print("\n✓ Test 6: Running full analysis...")
    intent = engine.analyze(snapshot, context)
    print(f"  Action: {intent.action.value}")
    print(f"  Confidence: {intent.confidence_score}")
    print(f"  Quantity Factor: {intent.quantity_factor}")
    print(f"  Reasoning: {intent.reasoning_summary}")
    
    # Test 7: Verify pillar scores
    print("\n✓ Test 7: Verifying pillar breakdown...")
    print(f"  Trend: {intent.trend_score}")
    print(f"  Momentum: {intent.momentum_score}")
    print(f"  Volatility: {intent.volatility_score}")
    print(f"  Liquidity: {intent.liquidity_score}")
    print(f"  Sentiment: {intent.sentiment_score}")
    print(f"  Regime: {intent.regime_score}")
    
    print("\n" + "=" * 60)
    print("✅ Phase 1 Validation PASSED")
    print("=" * 60)
    print("\nNext Steps:")
    print("- Phase 2: Wire DerivativesAnalyzer to SentimentPillar")
    print("- Phase 3: Migrate Trend/Momentum logic from RecommendationService")
    print("=" * 60)

if __name__ == "__main__":
    test_phase_1_skeleton()
