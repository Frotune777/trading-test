from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class LiveDecisionSnapshot:
    """
    Snapshot of a single instrument at a point in time.
    HOT PATH data only - used for real-time decisions.
    """
    # Identity
    symbol: str
    timestamp: datetime
    
    # Price State
    ltp: float  # Last Traded Price
    vwap: float
    open: float
    high: float
    low: float
    prev_close: float
    
    # Liquidity State (L2 Depth)
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    bid_qty: Optional[int] = None
    ask_qty: Optional[int] = None
    spread_pct: Optional[float] = None  # (ask - bid) / ltp * 100
    
    # Derivative Greeks (if applicable)
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    oi_change: Optional[int] = None
    
    # Volume
    volume: int = 0
    delivery_pct: Optional[float] = None
    
    # Technical Indicators (for Trend/Momentum pillars)
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    sma_20_weekly: Optional[float] = None  # For weekly trend confirmation
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    
    # Volatility Indicators (for Volatility pillar)
    atr: Optional[float] = None              # Average True Range (absolute)
    atr_pct: Optional[float] = None          # ATR as % of close price
    bb_width: Optional[float] = None         # Bollinger Band width as % of middle band
    bb_upper: Optional[float] = None         # Upper Bollinger Band
    bb_middle: Optional[float] = None        # Middle Bollinger Band
    bb_lower: Optional[float] = None         # Lower Bollinger Band
    
    # Liquidity Indicators (for Liquidity pillar)
    adosc: Optional[float] = None            # Chaikin A/D Oscillator (volume-based)

@dataclass
class SessionContext:
    """
    Market-wide state. WARM PATH data.
    Refreshed less frequently (every 5-15 mins).
    """
    timestamp: datetime
    
    # Regime
    market_regime: str  # BULLISH, BEARISH, VOLATILE, SIDEWAYS
    
    # Volatility
    vix_level: float
    vix_percentile: Optional[float] = None  # 0-100
    
    # Breadth
    advance_decline_ratio: Optional[float] = None
    stocks_above_200dma: Optional[int] = None
    
    # Institutional Flow
    fii_net_value: Optional[float] = None  # Day's net FII flow
    dii_net_value: Optional[float] = None
