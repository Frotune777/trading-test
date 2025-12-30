"""
Strategy DSL (Domain-Specific Language)
Python-based custom strategy framework with safe execution
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class StrategyBase(ABC):
    """
    Base class for user-defined strategies.
    
    Provides built-in methods for indicators and signal generation.
    Users inherit from this class to create custom strategies.
    """
    
    def __init__(self, symbol: str, params: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy.
        
        Args:
            symbol: Trading symbol
            params: Strategy parameters
        """
        self.symbol = symbol
        self.params = params or {}
        self.position = 0  # Current position size
        self.entry_price = 0.0
        self.signals = []
        
        # Call user setup
        self.setup()
    
    @abstractmethod
    def setup(self):
        """
        User-defined setup method.
        Initialize strategy parameters here.
        """
        pass
    
    @abstractmethod
    def on_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        User-defined signal generation logic.
        
        Args:
            data: Historical price data (OHLCV)
            
        Returns:
            Signal dict with action, quantity, etc.
        """
        pass
    
    # Built-in indicator methods
    def sma(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Simple Moving Average"""
        return data['close'].rolling(window=period).mean()
    
    def ema(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return data['close'].ewm(span=period, adjust=False).mean()
    
    def rsi(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def macd(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD Indicator"""
        ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def bollinger_bands(self, data: pd.DataFrame, period: int = 20, std: float = 2.0) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = data['close'].rolling(window=period).mean()
        std_dev = data['close'].rolling(window=period).std()
        
        return {
            'upper': sma + (std_dev * std),
            'middle': sma,
            'lower': sma - (std_dev * std)
        }
    
    def atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        return true_range.rolling(window=period).mean()
    
    def stochastic(self, data: pd.DataFrame, period: int = 14) -> Dict[str, pd.Series]:
        """Stochastic Oscillator"""
        low_min = data['low'].rolling(window=period).min()
        high_max = data['high'].rolling(window=period).max()
        
        k = 100 * ((data['close'] - low_min) / (high_max - low_min))
        d = k.rolling(window=3).mean()
        
        return {'k': k, 'd': d}
    
    # Signal generation helpers
    def buy(self, quantity: int, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Dict[str, Any]:
        """Generate BUY signal"""
        return {
            'action': 'BUY',
            'symbol': self.symbol,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'timestamp': datetime.now().isoformat()
        }
    
    def sell(self, quantity: int, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Dict[str, Any]:
        """Generate SELL signal"""
        return {
            'action': 'SELL',
            'symbol': self.symbol,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'timestamp': datetime.now().isoformat()
        }
    
    def hold(self) -> Dict[str, Any]:
        """Generate HOLD signal"""
        return {
            'action': 'HOLD',
            'symbol': self.symbol,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_latest_price(self, data: pd.DataFrame) -> float:
        """Get latest close price"""
        return float(data['close'].iloc[-1])
    
    def get_position(self) -> int:
        """Get current position size"""
        return self.position
    
    def update_position(self, quantity: int, price: float):
        """Update position after trade execution"""
        self.position += quantity
        if self.position != 0:
            self.entry_price = price


# Example strategy implementations
class SMACrossoverStrategy(StrategyBase):
    """
    Simple Moving Average Crossover Strategy
    BUY when fast SMA crosses above slow SMA
    SELL when fast SMA crosses below slow SMA
    """
    
    def setup(self):
        self.fast_period = self.params.get('fast_period', 20)
        self.slow_period = self.params.get('slow_period', 50)
        self.quantity = self.params.get('quantity', 100)
    
    def on_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        # Calculate SMAs
        sma_fast = self.sma(data, self.fast_period)
        sma_slow = self.sma(data, self.slow_period)
        
        # Get latest values
        current_fast = sma_fast.iloc[-1]
        current_slow = sma_slow.iloc[-1]
        prev_fast = sma_fast.iloc[-2]
        prev_slow = sma_slow.iloc[-2]
        
        # Detect crossover
        if prev_fast <= prev_slow and current_fast > current_slow:
            # Bullish crossover
            return self.buy(quantity=self.quantity, stop_loss=0.02)
        elif prev_fast >= prev_slow and current_fast < current_slow:
            # Bearish crossover
            return self.sell(quantity=self.quantity)
        else:
            return self.hold()


class RSIMeanReversionStrategy(StrategyBase):
    """
    RSI Mean Reversion Strategy
    BUY when RSI < oversold threshold
    SELL when RSI > overbought threshold
    """
    
    def setup(self):
        self.rsi_period = self.params.get('rsi_period', 14)
        self.oversold = self.params.get('oversold', 30)
        self.overbought = self.params.get('overbought', 70)
        self.quantity = self.params.get('quantity', 100)
    
    def on_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        # Calculate RSI
        rsi = self.rsi(data, self.rsi_period)
        current_rsi = rsi.iloc[-1]
        
        # Generate signals
        if current_rsi < self.oversold and self.position == 0:
            return self.buy(quantity=self.quantity, take_profit=0.05)
        elif current_rsi > self.overbought and self.position > 0:
            return self.sell(quantity=self.position)
        else:
            return self.hold()


class MACDStrategy(StrategyBase):
    """
    MACD Strategy
    BUY when MACD crosses above signal line
    SELL when MACD crosses below signal line
    """
    
    def setup(self):
        self.fast = self.params.get('fast', 12)
        self.slow = self.params.get('slow', 26)
        self.signal = self.params.get('signal', 9)
        self.quantity = self.params.get('quantity', 100)
    
    def on_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        # Calculate MACD
        macd_data = self.macd(data, self.fast, self.slow, self.signal)
        
        current_macd = macd_data['macd'].iloc[-1]
        current_signal = macd_data['signal'].iloc[-1]
        prev_macd = macd_data['macd'].iloc[-2]
        prev_signal = macd_data['signal'].iloc[-2]
        
        # Detect crossover
        if prev_macd <= prev_signal and current_macd > current_signal:
            return self.buy(quantity=self.quantity, stop_loss=0.02)
        elif prev_macd >= prev_signal and current_macd < current_signal:
            return self.sell(quantity=self.quantity)
        else:
            return self.hold()
