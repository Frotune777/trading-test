import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Add backend to path
sys.path.append(os.getcwd())

from backend.app.reasoning.reasoning_engine import ReasoningEngine
from backend.app.reasoning.snapshot_builder import SnapshotBuilder
from backend.app.core.market_snapshot import LiveDecisionSnapshot, SessionContext

def test_data_age():
    print("Testing data age calculation...")
    from backend.app.reasoning.pillars.volatility_pillar import VolatilityPillar
    from backend.app.reasoning.pillars.liquidity_pillar import LiquidityPillar
    
    engine = ReasoningEngine()
    engine.register_pillar('volatility', VolatilityPillar())
    engine.register_pillar('liquidity', LiquidityPillar())
    
    # Create a snapshot with a 1-minute old timestamp
    old_ts = datetime.now() - timedelta(minutes=1)
    snapshot = LiveDecisionSnapshot(
        symbol="RELIANCE",
        timestamp=old_ts,
        ltp=2500.0,
        vwap=2500.0,
        open=2500.0,
        high=2510.0,
        low=2490.0,
        prev_close=2480.0,
        volume=1000000,
        atr_pct=2.0,
        bb_width=5.0
    )
    
    context = SessionContext(
        timestamp=datetime.now(),
        market_regime="BULLISH",
        vix_level=15.0
    )
    
    intent = engine.analyze(snapshot, context)
    print(f"  Pillar contributions: {len(intent.pillar_contributions)}")
    print(f"  Data age: {intent.quality.data_age_seconds} seconds")
    
    assert intent.quality.data_age_seconds is not None
    assert 50 <= intent.quality.data_age_seconds <= 70
    print("  ✅ Data age test passed!")

def test_vix_and_weekly():
    print("\nTesting VIX and weekly data fetch...")
    builder = SnapshotBuilder()
    
    # Test VIX fetch
    try:
        context = builder.build_session_context()
        print(f"  Fetched VIX Level: {context.vix_level:.2f}")
        print(f"  VIX Percentile: {context.vix_percentile:.2f}%")
        assert context.vix_level > 0
        print("  ✅ VIX fetch test passed!")
    except Exception as e:
        print(f"  ❌ VIX fetch failed: {e}")

    # Test Weekly SMA fetch
    try:
        snapshot = builder.build_snapshot("RELIANCE")
        print(f"  Fetched Weekly SMA 20: {snapshot.sma_20_weekly}")
        # Note: can be None if it's weekend or data unavailable, but we expect it for RELIANCE
        if snapshot.sma_20_weekly:
             print("  ✅ Weekly SMA fetch test passed!")
        else:
             print("  ⚠️ Weekly SMA is None (check connectivity/market hours)")
    except Exception as e:
        print(f"  ❌ Weekly SMA fetch failed: {e}")

if __name__ == "__main__":
    try:
        test_data_age()
        test_vix_and_weekly()
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        sys.exit(1)
