"""
FeedCrossValidator Service
Cross-validates data between OpenAlgo and local TA-Lib calculations.

This service compares indicators from multiple sources to detect divergence
and prevent bad data from influencing trading decisions.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
import pandas as pd
import talib

from app.core.market_snapshot import LiveDecisionSnapshot

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of cross-validation between data sources."""
    is_valid: bool
    warnings: List[str]
    divergences: Dict[str, float]  # indicator -> divergence amount
    source_comparison: Dict[str, Dict[str, float]]  # indicator -> {source1: val, source2: val}


class FeedCrossValidator:
    """
    Compares indicators from multiple sources:
    - OpenAlgo API (external)
    - Local TA-Lib calculations (internal)
    
    Detects divergence to prevent bad data from influencing decisions.
    """
    
    # Tolerance thresholds
    TOLERANCE_RSI = 2.0  # ±2 points acceptable
    TOLERANCE_SMA_PCT = 0.5  # ±0.5% acceptable
    TOLERANCE_MACD_PCT = 5.0  # ±5% acceptable (MACD can be small values)
    TOLERANCE_ATR_PCT = 10.0  # ±10% acceptable (ATR varies more)
    
    def __init__(self):
        """Initialize cross-validator."""
        self.validation_cache = {}  # Cache recent validations
    
    async def validate_indicators(
        self, 
        symbol: str, 
        snapshot: LiveDecisionSnapshot,
        ohlcv_data: Optional[pd.DataFrame] = None
    ) -> ValidationResult:
        """
        Compares snapshot indicators against local calculations.
        
        Args:
            symbol: Symbol being validated
            snapshot: Current market snapshot with indicators
            ohlcv_data: Optional OHLCV dataframe for local calculations
            
        Returns:
            ValidationResult with warnings if divergence exceeds tolerance
        """
        warnings = []
        divergences = {}
        comparisons = {}
        
        # If no OHLCV data provided, we can't validate
        if ohlcv_data is None or len(ohlcv_data) < 50:
            warnings.append("Insufficient OHLCV data for cross-validation")
            return ValidationResult(
                is_valid=True,  # Don't block if we can't validate
                warnings=warnings,
                divergences={},
                source_comparison={}
            )
        
        # Calculate local indicators
        local_indicators = self.calculate_local_indicators(ohlcv_data)
        print("DEBUG SOURCE LOCAL INDICATORS:", local_indicators)
        
        # Validate RSI
        if snapshot.rsi is not None and local_indicators.get('rsi') is not None:
            rsi_diff = abs(snapshot.rsi - local_indicators['rsi'])
            divergences['rsi'] = rsi_diff
            comparisons['rsi'] = {
                'openalgo': snapshot.rsi,
                'local': local_indicators['rsi']
            }
            
            if rsi_diff > self.TOLERANCE_RSI:
                warnings.append(
                    f"RSI divergence: OpenAlgo={snapshot.rsi:.1f}, "
                    f"Local={local_indicators['rsi']:.1f} (diff={rsi_diff:.1f})"
                )
        
        # Validate SMA 50
        if snapshot.sma_50 is not None and local_indicators.get('sma_50') is not None:
            sma50_pct_diff = abs((snapshot.sma_50 - local_indicators['sma_50']) / local_indicators['sma_50'] * 100)
            divergences['sma_50'] = sma50_pct_diff
            comparisons['sma_50'] = {
                'openalgo': snapshot.sma_50,
                'local': local_indicators['sma_50']
            }
            
            if sma50_pct_diff > self.TOLERANCE_SMA_PCT:
                warnings.append(
                    f"SMA50 divergence: OpenAlgo={snapshot.sma_50:.2f}, "
                    f"Local={local_indicators['sma_50']:.2f} ({sma50_pct_diff:.2f}%)"
                )
        
        # Validate SMA 200
        if snapshot.sma_200 is not None and local_indicators.get('sma_200') is not None:
            sma200_pct_diff = abs((snapshot.sma_200 - local_indicators['sma_200']) / local_indicators['sma_200'] * 100)
            divergences['sma_200'] = sma200_pct_diff
            comparisons['sma_200'] = {
                'openalgo': snapshot.sma_200,
                'local': local_indicators['sma_200']
            }
            
            if sma200_pct_diff > self.TOLERANCE_SMA_PCT:
                warnings.append(
                    f"SMA200 divergence: OpenAlgo={snapshot.sma_200:.2f}, "
                    f"Local={local_indicators['sma_200']:.2f} ({sma200_pct_diff:.2f}%)"
                )
        
        # Validate MACD
        if snapshot.macd is not None and local_indicators.get('macd') is not None:
            # MACD can be close to zero, so use absolute difference if values are small
            if abs(local_indicators['macd']) < 1.0:
                macd_diff = abs(snapshot.macd - local_indicators['macd'])
                if macd_diff > 0.5:  # Absolute tolerance for small values
                    warnings.append(
                        f"MACD divergence: OpenAlgo={snapshot.macd:.3f}, "
                        f"Local={local_indicators['macd']:.3f}"
                    )
            else:
                macd_pct_diff = abs((snapshot.macd - local_indicators['macd']) / local_indicators['macd'] * 100)
                divergences['macd'] = macd_pct_diff
                comparisons['macd'] = {
                    'openalgo': snapshot.macd,
                    'local': local_indicators['macd']
                }
                
                if macd_pct_diff > self.TOLERANCE_MACD_PCT:
                    warnings.append(
                        f"MACD divergence: OpenAlgo={snapshot.macd:.3f}, "
                        f"Local={local_indicators['macd']:.3f} ({macd_pct_diff:.2f}%)"
                    )
        
        # Validate ATR
        if snapshot.atr_pct is not None and local_indicators.get('atr_pct') is not None:
            atr_pct_diff = abs((snapshot.atr_pct - local_indicators['atr_pct']) / local_indicators['atr_pct'] * 100)
            divergences['atr_pct'] = atr_pct_diff
            comparisons['atr_pct'] = {
                'openalgo': snapshot.atr_pct,
                'local': local_indicators['atr_pct']
            }
            
            if atr_pct_diff > self.TOLERANCE_ATR_PCT:
                warnings.append(
                    f"ATR divergence: OpenAlgo={snapshot.atr_pct:.2f}%, "
                    f"Local={local_indicators['atr_pct']:.2f}% ({atr_pct_diff:.2f}%)"
                )
        
        # Determine if validation passed
        is_valid = len(warnings) == 0
        
        if not is_valid:
            logger.warning(f"Cross-validation failed for {symbol}: {len(warnings)} divergences detected")
        
        return ValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            divergences=divergences,
            source_comparison=comparisons
        )
    
    def calculate_local_indicators(self, ohlcv_data: pd.DataFrame) -> Dict[str, float]:
        """
        Uses TA-Lib to independently calculate indicators.
        
        Args:
            ohlcv_data: DataFrame with columns: open, high, low, close, volume
            
        Returns:
            Dictionary of calculated indicators
        """
        indicators = {}
        
        try:
            close = ohlcv_data['close'].values
            high = ohlcv_data['high'].values
            low = ohlcv_data['low'].values
            
            # RSI (14-period)
            if len(close) >= 14:
                rsi = talib.RSI(close, timeperiod=14)
                indicators['rsi'] = float(rsi[-1]) if not pd.isna(rsi[-1]) else None
            
            # SMA 50
            if len(close) >= 50:
                sma50 = talib.SMA(close, timeperiod=50)
                indicators['sma_50'] = float(sma50[-1]) if not pd.isna(sma50[-1]) else None
            
            # SMA 200
            if len(close) >= 200:
                sma200 = talib.SMA(close, timeperiod=200)
                indicators['sma_200'] = float(sma200[-1]) if not pd.isna(sma200[-1]) else None
            
            # MACD
            if len(close) >= 26:
                macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
                indicators['macd'] = float(macd[-1]) if not pd.isna(macd[-1]) else None
                indicators['macd_signal'] = float(macd_signal[-1]) if not pd.isna(macd_signal[-1]) else None
                indicators['macd_hist'] = float(macd_hist[-1]) if not pd.isna(macd_hist[-1]) else None
            
            # ATR (14-period)
            if len(close) >= 14:
                atr = talib.ATR(high, low, close, timeperiod=14)
                if not pd.isna(atr[-1]) and close[-1] > 0:
                    indicators['atr_pct'] = float((atr[-1] / close[-1]) * 100)
            
        except Exception as e:
            logger.error(f"Error calculating local indicators: {e}")
        
        return indicators
