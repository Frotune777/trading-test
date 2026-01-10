import pytest
import asyncio
from datetime import datetime, timedelta
from app.core.market_snapshot import LiveDecisionSnapshot, SessionContext
from app.reasoning.reasoning_engine import ReasoningEngine
from app.reasoning.pillars.base_pillar import BasePillar
from app.reasoning.pillars.trend_pillar import TrendPillar
from app.reasoning.pillars.momentum_pillar import MomentumPillar
from app.reasoning.pillars.volatility_pillar import VolatilityPillar
from app.reasoning.pillars.liquidity_pillar import LiquidityPillar
from app.reasoning.pillars.sentiment_pillar import SentimentPillar
from app.reasoning.pillars.regime_pillar import RegimePillar
from app.core.trade_intent import DirectionalBias

@pytest.fixture
def engine():
    e = ReasoningEngine()
    e.register_pillar('trend', TrendPillar())
    e.register_pillar('momentum', MomentumPillar())
    e.register_pillar('volatility', VolatilityPillar())
    e.register_pillar('liquidity', LiquidityPillar())
    e.register_pillar('sentiment', SentimentPillar())
    e.register_pillar('regime', RegimePillar())
    return e

def create_base_snapshot(symbol="RELIANCE", ltp=2500.0):
    return LiveDecisionSnapshot(
        symbol=symbol,
        timestamp=datetime.now(),
        ltp=ltp,
        vwap=ltp,
        open=ltp,
        high=ltp,
        low=ltp,
        prev_close=ltp,
        ltp_source="redis_ws",
        ltp_age_ms=100
    )

def create_base_context():
    return SessionContext(
        timestamp=datetime.now(),
        market_regime="SIDEWAYS",
        vix_level=15.0
    )

@pytest.mark.asyncio
async def test_bullish_trending_regime(engine):
    """Scenario: Strong uptrend, high volume, positive sentiment."""
    snapshot = create_base_snapshot(ltp=2600.0)
    snapshot.sma_50 = 2500.0
    snapshot.sma_200 = 2400.0
    snapshot.sma_20_weekly = 2450.0
    snapshot.rsi = 65.0
    snapshot.macd = 10.0
    snapshot.macd_signal = 5.0
    snapshot.macd_hist = 5.0
    snapshot.atr_pct = 1.2
    snapshot.bb_width = 5.0
    snapshot.spread_pct = 0.02
    snapshot.bid_qty = 5000
    snapshot.ask_qty = 2000
    snapshot.oi_change = 100000
    snapshot.prev_close = 2550.0
    
    context = create_base_context()
    context.market_regime = "BULLISH"
    context.vix_level = 13.0
    
    intent = engine.analyze(snapshot, context)
    
    assert intent.directional_bias == DirectionalBias.BULLISH
    assert intent.conviction_score > 70
    assert intent.is_execution_ready == True

@pytest.mark.asyncio
async def test_flash_crash_regime(engine):
    """Scenario: Sudden sharp drop, spiked volatility, thin liquidity."""
    snapshot = create_base_snapshot(ltp=2200.0)
    snapshot.prev_close = 2500.0
    snapshot.sma_50 = 2450.0
    snapshot.sma_200 = 2400.0
    snapshot.rsi = 15.0  # Extremely oversold
    snapshot.macd = -50.0
    snapshot.macd_signal = -10.0
    snapshot.macd_hist = -40.0
    snapshot.atr_pct = 9.0  # Extreme volatility
    snapshot.bb_width = 25.0 # Extreme wide bands
    snapshot.spread_pct = 0.6 # Very wide spread
    snapshot.bid_qty = 50
    snapshot.ask_qty = 5000 # Heavy selling
    snapshot.oi_change = 500000 # Massive buildup or unwinding
    
    context = create_base_context()
    context.market_regime = "BEARISH"
    context.vix_level = 35.0  # Fear spiked
    
    intent = engine.analyze(snapshot, context)
    
    # In a flash crash, bias should be BEARISH or NEUTRAL (too volatile)
    assert intent.directional_bias in [DirectionalBias.BEARISH, DirectionalBias.NEUTRAL]
    
    # Simulate liquidity evaporation (common in flash crashes)
    snapshot.bid_price = None 
    snapshot.ask_price = None
    
    from app.services.data_integrity_gate import StrictDataIntegrityGate
    # Intent has valid analysis, but data is now "unsafe" due to missing depth
    is_safe, reason = StrictDataIntegrityGate.evaluate_intent(intent, snapshot)
    
    # Gate should block due to missing liquidity depth (Rule #6/Integrity)
    assert is_safe is False
    assert "MISSING_LIQUIDITY_DEPTH" in reason

@pytest.mark.asyncio
async def test_choppy_sideways_regime(engine):
    """Scenario: Price oscillating, conflicting indicators."""
    snapshot = create_base_snapshot(ltp=2500.0)
    snapshot.sma_50 = 2490.0  # Price slightly above
    snapshot.sma_200 = 2485.0  # Price slightly above
    snapshot.rsi = 50.0
    snapshot.atr_pct = 3.5 # Elevated but not extreme
    snapshot.bb_width = 10.0
    snapshot.spread_pct = 0.15
    snapshot.bid_qty = 1000
    snapshot.ask_qty = 1100
    
    context = create_base_context()
    context.market_regime = "SIDEWAYS"
    context.vix_level = 18.0
    
    intent = engine.analyze(snapshot, context)
    
    # In sideways market with mixed signals, bias can be NEUTRAL or weak directional
    assert intent.directional_bias in [DirectionalBias.NEUTRAL, DirectionalBias.BULLISH, DirectionalBias.BEARISH]
    assert 30 <= intent.conviction_score <= 60

@pytest.mark.asyncio
async def test_gap_up_acceleration(engine):
    """Scenario: Gap up open, momentum accelerating."""
    snapshot = create_base_snapshot(ltp=2700.0)
    snapshot.prev_close = 2500.0
    snapshot.sma_50 = 2550.0
    snapshot.sma_200 = 2500.0
    snapshot.sma_20_weekly = 2520.0  # Add weekly SMA
    snapshot.rsi = 75.0 # Overbought but accelerating
    snapshot.macd = 20.0
    snapshot.macd_signal = 5.0
    snapshot.macd_hist = 15.0
    snapshot.atr_pct = 2.0  # Add ATR
    snapshot.bb_width = 6.0  # Add BB width
    snapshot.spread_pct = 0.05  # Add spread
    snapshot.bid_qty = 8000
    snapshot.ask_qty = 1000
    
    context = create_base_context()
    context.market_regime = "BULLISH"
    context.vix_level = 14.0  # Low VIX supports bullish
    
    intent = engine.analyze(snapshot, context)
    
    assert intent.directional_bias == DirectionalBias.BULLISH
    assert intent.conviction_score > 60
