"""
Snapshot Builder - Converts existing data sources to LiveDecisionSnapshot
"""

from datetime import datetime
from typing import Optional
import pandas as pd
from ..core.market_snapshot import LiveDecisionSnapshot, SessionContext
from ..services.technical_analysis import TechnicalAnalysisService
from ..services.market_regime import MarketRegime
from ..data_sources.nse_master_data import NSEMasterData

class SnapshotBuilder:
    """
    Builds LiveDecisionSnapshot and SessionContext from existing data sources.
    Acts as an adapter between old data services and new reasoning engine.
    """
    
    def __init__(self):
        self.nse_master = NSEMasterData()
    
    def build_snapshot(
        self, 
        symbol: str,
        price_df: Optional[pd.DataFrame] = None,
        option_data: Optional[dict] = None
    ) -> LiveDecisionSnapshot:
        """
        Build a LiveDecisionSnapshot for a symbol.
        
        Args:
            symbol: Stock symbol
            price_df: Historical OHLCV DataFrame (optional, will fetch if None)
            option_data: Option chain data dict (optional)
            
        Returns:
            LiveDecisionSnapshot with all available data
        """
        # Fetch price data if not provided
        if price_df is None or price_df.empty:
            # Fetch last 100 days for indicator calculation
            price_df = self.nse_master.get_history(
                symbol=symbol,
                exchange="NSE",
                interval="1d"
            )
        
        if price_df is None or price_df.empty:
            raise ValueError(f"No price data available for {symbol}")
        
        # Calculate technical indicators
        ta = TechnicalAnalysisService(price_df)
        ta.add_trend_indicators()
        ta.add_momentum_indicators()
        ta.add_volatility_indicators()  # NEW: ATR and Bollinger Bands
        df = ta.df
        
        # Get latest values
        current = df.iloc[-1]
        
        # Extract price state
        ltp = float(current['close'])
        open_price = float(current['open'])
        high = float(current['high'])
        low = float(current['low'])
        volume = int(current['volume'])
        
        # Previous close (from second-to-last row)
        prev_close = float(df.iloc[-2]['close']) if len(df) > 1 else ltp
        
        # Calculate VWAP (simple approximation)
        vwap = (high + low + ltp) / 3.0
        
        # Extract technical indicators (Trend/Momentum)
        sma_50 = float(current.get('sma_50', ltp))
        sma_200 = float(current.get('sma_200', ltp))
        rsi = float(current.get('rsi', 50.0))
        macd = float(current.get('macd', 0.0))
        macd_signal = float(current.get('macd_signal', 0.0))
        macd_hist = float(current.get('macd_hist', 0.0))
        
        # Extract volatility indicators
        atr = float(current.get('atr', 0.0))
        atr_pct = (atr / ltp * 100.0) if ltp > 0 and atr > 0 else 0.0
        
        bb_upper = current.get('bb_upper')
        bb_middle = current.get('bb_middle')
        bb_lower = current.get('bb_lower')
        bb_width = None
        if bb_upper is not None and bb_lower is not None and bb_middle is not None and bb_middle > 0:
            bb_width = ((bb_upper - bb_lower) / bb_middle * 100.0)
        
        # Extract liquidity indicators
        adosc = current.get('adosc')
        
        # Weekly SMA (fetch weekly data separately or approximate)
        sma_20_weekly = None  # TODO: Implement weekly data fetch
        
        # Extract derivatives data if available
        delta = None
        gamma = None
        theta = None
        vega = None
        oi_change = None
        
        if option_data:
            # Extract from option data dict
            delta = option_data.get('delta')
            gamma = option_data.get('gamma')
            theta = option_data.get('theta')
            vega = option_data.get('vega')
            oi_change = option_data.get('oi_change')
        
        return LiveDecisionSnapshot(
            symbol=symbol,
            timestamp=datetime.now(),
            ltp=ltp,
            vwap=vwap,
            open=open_price,
            high=high,
            low=low,
            prev_close=prev_close,
            volume=volume,
            sma_50=sma_50,
            sma_200=sma_200,
            sma_20_weekly=sma_20_weekly,
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            macd_hist=macd_hist,
            atr=atr,
            atr_pct=atr_pct,
            bb_width=bb_width,
            bb_upper=float(bb_upper) if bb_upper is not None else None,
            bb_middle=float(bb_middle) if bb_middle is not None else None,
            bb_lower=float(bb_lower) if bb_lower is not None else None,
            adosc=float(adosc) if adosc is not None else None,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            oi_change=oi_change
        )
    
    def build_session_context(
        self,
        nifty_df: Optional[pd.DataFrame] = None
    ) -> SessionContext:
        """
        Build SessionContext from market-wide data.
        
        Args:
            nifty_df: NIFTY 50 historical data (optional, will fetch if None)
            
        Returns:
            SessionContext with market regime and VIX
        """
        # Fetch NIFTY data if not provided
        if nifty_df is None or nifty_df.empty:
            nifty_df = self.nse_master.get_history(
                symbol="NIFTY 50",
                exchange="NSE",
                interval="1d"
            )
        
        # Determine market regime
        regime = "NEUTRAL"
        if nifty_df is not None and not nifty_df.empty:
            market_regime_analyzer = MarketRegime(nifty_df)
            regime_data = market_regime_analyzer.determine_regime()
            regime = regime_data.get('direction', 'NEUTRAL')
        
        # Get VIX (hardcoded for now, should fetch from data source)
        vix_level = 15.0  # TODO: Fetch real VIX from India VIX index
        
        return SessionContext(
            timestamp=datetime.now(),
            market_regime=regime,
            vix_level=vix_level,
            vix_percentile=50.0
        )
