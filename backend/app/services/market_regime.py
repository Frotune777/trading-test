import pandas as pd
import numpy as np
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


class MarketRegimeDetector:
    """
    Enhanced market regime detector with granular classification.
    
    Regimes:
    - TRENDING_UP: Strong uptrend
    - TRENDING_DOWN: Strong downtrend
    - RANGING: Sideways/consolidation
    - VOLATILE: High volatility, uncertain direction
    """
    
    def detect_regime(self, data: pd.DataFrame) -> str:
        """
        Detect current market regime.
        
        Args:
            data: Historical OHLCV data
            
        Returns:
            Regime string
        """
        try:
            # Calculate indicators
            ta = TechnicalAnalysisService(data)
            ta.add_trend_indicators()
            ta.add_volatility_indicators()
            
            df = ta.df
            
            # Get latest values
            adx = df['adx'].iloc[-1] if 'adx' in df.columns else 20
            close = df['close'].iloc[-1]
            sma_20 = df['sma_20'].iloc[-1] if 'sma_20' in df.columns else close
            sma_50 = df['sma_50'].iloc[-1] if 'sma_50' in df.columns else close
            
            # Volatility
            atr = df['atr'].iloc[-1] if 'atr' in df.columns else 0
            atr_ma = df['atr'].rolling(window=14).mean().iloc[-1] if 'atr' in df.columns else 1
            
            # Determine regime
            is_trending = adx > 25
            is_volatile = atr > atr_ma * 1.5
            is_uptrend = close > sma_20 > sma_50
            is_downtrend = close < sma_20 < sma_50
            
            if is_volatile:
                return "VOLATILE"
            elif is_trending and is_uptrend:
                return "TRENDING_UP"
            elif is_trending and is_downtrend:
                return "TRENDING_DOWN"
            else:
                return "RANGING"
                
        except Exception as e:
            return "UNKNOWN"
