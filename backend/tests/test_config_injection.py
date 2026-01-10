import pytest
import asyncio
from datetime import datetime
from app.reasoning.reasoning_engine import ReasoningEngine
from app.reasoning.pillar_config import PillarConfig
from app.reasoning.pillars.trend_pillar import TrendPillar
from app.core.market_snapshot import LiveDecisionSnapshot, SessionContext

@pytest.mark.asyncio
async def test_pillar_config_injection():
    # 1. Setup Engine & Pillar
    engine = ReasoningEngine()
    engine.register_pillar("trend", TrendPillar())
    
    # 2. Setup Snapshot
    snapshot = LiveDecisionSnapshot(
        symbol="TEST",
        ltp=100.0,
        timestamp=datetime.now(),
        prev_close=98.0,
        open=99.0,
        high=101.0,
        low=99.0,
        vwap=100.0,
        sma_50=105.0,   # below
        sma_200=95.0,   # above
        # Need weekly for trend pillar not to crash?
        # TrendPillar checks: if snapshot.sma_20_weekly:
        sma_20_weekly=None 
    )
    
    context = SessionContext(
        timestamp=datetime.now(),
        market_regime="BULLISH",
        vix_level=12.0
    )
    
    # 3. Create Config Override
    # Default short is 50. Let's override to 10.
    config = PillarConfig(
        trend_sma_short=10,
        trend_sma_long=50
    )
    
    # 4. Analyze with Config
    intent = engine.analyze(snapshot, context, pillar_config=config)
    
    # 5. Verify Metrics
    # TrendPillar output metrics: f"SMA {sma_short_period}"
    # If override worked, we should see "SMA 10" in metrics.
    
    metrics = intent.pillar_contributions[0].metrics
    print(metrics)
    
    assert "SMA 10" in metrics, f"Expected 'SMA 10' in metrics, got {metrics.keys()}"
    assert "SMA 50" in metrics, f"Expected 'SMA 50' in metrics, got {metrics.keys()}"
    
    # Verify no "SMA 200" (default long)
    assert "SMA 200" not in metrics, "Did not expect default SMA 200 in metrics"

@pytest.mark.asyncio
async def test_pillar_config_defaults():
    # Verify defaults still work
    engine = ReasoningEngine()
    engine.register_pillar("trend", TrendPillar())
    
    snapshot = LiveDecisionSnapshot(
        symbol="TEST",
        ltp=100.0,
        timestamp=datetime.now(),
        prev_close=98.0,
        open=99.0,
        high=101.0,
        low=99.0,
        vwap=100.0,
        sma_50=105.0,
        sma_200=95.0
    )
    
    context = SessionContext(timestamp=datetime.now(), market_regime="BULLISH", vix_level=12.0)
    
    intent = engine.analyze(snapshot, context) # No config
    
    metrics = intent.pillar_contributions[0].metrics
    
    # Expect defaults: SMA 50, SMA 200
    assert "SMA 50" in metrics
    assert "SMA 200" in metrics
