from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class PillarConfig:
    """
    Configuration overrides for QUAD pillars.
    Allows injecting dynamic thresholds (e.g., from Backtesting engine or ML model).
    
    If a field is None, the pillar should fall back to global settings.
    """
    # Trend Pillar
    trend_sma_short: Optional[int] = None
    trend_sma_long: Optional[int] = None
    
    # Momentum Pillar
    rsi_period: Optional[int] = None
    rsi_overbought: Optional[float] = None
    rsi_oversold: Optional[float] = None
    
    # Volatility Pillar
    atr_period: Optional[int] = None
    
    # Generic overrides map for flexibility
    overrides: Dict[str, Any] = field(default_factory=dict)
