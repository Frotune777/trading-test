import pandas as pd
from typing import Dict, Any, Tuple
from .technical_analysis import TechnicalAnalysisService

class MarketRegime:
    """
    Analyzes Market Condition (Trend vs Range).
    Uses NIFTY 50 as benchmark.
    """
    
    def __init__(self, index_df: pd.DataFrame):
        """
        index_df: DataFrame with OHLCV for Nifty 50.
        """
        self.df = index_df
        
    def determine_regime(self) -> Dict[str, Any]:
        """
        Detects if market is TRENDING or SIDEWAYS/VOLATILE.
        Returns: Dict with regime, adx, trend_direction.
        """
        if self.df is None or self.df.empty:
            return {'regime': 'UNKNOWN', 'score': 0.5}
            
        ta = TechnicalAnalysisService(self.df)
        ta.add_trend_indicators() # Adds SMA, EMA, ADX
        
        # Ensure ADX is calculated
        if 'adx_14' not in ta.df.columns:
            # Manually trigger if add_trend_indicators didn't (it should)
            pass
            
        row = ta.df.iloc[-1]
        
        adx = row.get('adx_14', 20)
        close = row['close']
        sma_50 = row.get('sma_50', close)
        sma_200 = row.get('sma_200', close)
        
        # 1. Regime Classification (ADX)
        if adx > 25:
            regime = 'TRENDING'
        else:
            regime = 'SIDEWAYS'
            
        # 2. Trend Direction
        direction = 'NEUTRAL'
        if close > sma_50 > sma_200:
            direction = 'BULLISH'
        elif close < sma_50 < sma_200:
            direction = 'BEARISH'
            
        return {
            'regime': regime,
            'direction': direction,
            'adx': round(adx, 2),
            'market_score': 100 if direction == 'BULLISH' else 0 if direction == 'BEARISH' else 50
        }
