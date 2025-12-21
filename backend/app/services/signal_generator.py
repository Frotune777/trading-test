from enum import Enum
from typing import List, Dict, Any
import pandas as pd
from .technical_analysis import TechnicalAnalysisService

class SignalType(Enum):
    TREND = "TREND"
    MOMENTUM = "MOMENTUM"
    VOLATILITY = "VOLATILITY"
    REVERSAL = "REVERSAL"

class SignalGenerator:
    """
    PILLAR 3: Decision Engine (D)
    Generates trading signals based on technical indicators.
    """
    def __init__(self, analyzed_df: pd.DataFrame):
        self.df = analyzed_df

    def generate_signals(self) -> List[Dict[str, Any]]:
        if self.df is None or self.df.empty:
            return []
            
        latest = self.df.iloc[-1]
        signals = []
        
        # Risk Management Params
        atr = latest.get('atr', latest['close'] * 0.02) # Default 2% if missing ATR
        close = latest['close']

        # 1. RSI Signal
        rsi = latest.get('rsi')
        if rsi:
            if rsi < 30:
                signals.append(self._create_signal(
                    SignalType.MOMENTUM, "BUY", "RSI Oversold", close, atr, 1.5
                ))
            elif rsi > 70:
                signals.append(self._create_signal(
                    SignalType.MOMENTUM, "SELL", "RSI Overbought", close, atr, 1.5
                ))

        # 2. Moving Average Cross
        # Golden Cross (20 crossing above 50)
        if len(self.df) > 1:
            prev = self.df.iloc[-2]
            if (latest.get('sma_20') and latest.get('sma_50') and 
                latest['sma_20'] > latest['sma_50'] and prev['sma_20'] <= prev['sma_50']):
                signals.append(self._create_signal(
                    SignalType.TREND, "BUY", "Golden Cross (20/50)", close, atr, 2.0
                ))

        # 3. Bollinger Band Signal (Reversal)
        if latest.get('bb_lower') and latest['close'] < latest['bb_lower']:
             signals.append(self._create_signal(
                SignalType.VOLATILITY, "BUY", "Price below BB Lower", close, atr, 2.0
            ))
            
        return signals

    def _create_signal(self, sig_type: SignalType, action: str, reason: str, price: float, atr: float, rr_ratio: float = 2.0) -> Dict:
        """Create a structured signal with SL/Target."""
        
        # Stop Loss: 2 * ATR
        # Target: Risk * Ratio
        
        risk = 2 * atr
        
        if action == "BUY":
            sl = price - risk
            target = price + (risk * rr_ratio)
        else: # SELL
            sl = price + risk
            target = price - (risk * rr_ratio)
            
        return {
            "type": sig_type.value,
            "action": action,
            "reason": reason,
            "entry_price": round(price, 2),
            "stop_loss": round(sl, 2),
            "target_price": round(target, 2),
            "risk_reward": rr_ratio
        }
