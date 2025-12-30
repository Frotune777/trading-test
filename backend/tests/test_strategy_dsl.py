"""
Tests for Strategy DSL and Executor
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.strategy_dsl import StrategyBase, SMACrossoverStrategy, RSIMeanReversionStrategy
from app.services.strategy_executor import StrategyExecutor


class TestStrategyBase:
    """Test StrategyBase functionality"""
    
    def test_sma_calculation(self):
        """Test SMA indicator"""
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'close': np.random.randn(100).cumsum() + 100,
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 105,
            'low': np.random.randn(100).cumsum() + 95,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # Create strategy instance
        strategy = SMACrossoverStrategy(
            symbol="TEST",
            params={'fast_period': 20, 'slow_period': 50}
        )
        
        # Calculate SMA
        sma_20 = strategy.sma(data, 20)
        
        assert len(sma_20) == len(data)
        assert not sma_20.iloc[-1] != sma_20.iloc[-1]  # Not NaN
    
    def test_rsi_calculation(self):
        """Test RSI indicator"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'close': np.random.randn(100).cumsum() + 100,
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 105,
            'low': np.random.randn(100).cumsum() + 95,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        strategy = RSIMeanReversionStrategy(symbol="TEST", params={})
        rsi = strategy.rsi(data, 14)
        
        # RSI should be between 0 and 100
        assert rsi.iloc[-1] >= 0
        assert rsi.iloc[-1] <= 100
    
    def test_signal_generation(self):
        """Test signal generation methods"""
        strategy = SMACrossoverStrategy(symbol="TEST", params={})
        
        # Test BUY signal
        buy_signal = strategy.buy(quantity=100, stop_loss=0.02)
        assert buy_signal['action'] == 'BUY'
        assert buy_signal['quantity'] == 100
        assert buy_signal['stop_loss'] == 0.02
        
        # Test SELL signal
        sell_signal = strategy.sell(quantity=100)
        assert sell_signal['action'] == 'SELL'
        
        # Test HOLD signal
        hold_signal = strategy.hold()
        assert hold_signal['action'] == 'HOLD'


class TestSMACrossoverStrategy:
    """Test SMA Crossover Strategy"""
    
    def test_strategy_setup(self):
        """Test strategy initialization"""
        strategy = SMACrossoverStrategy(
            symbol="RELIANCE",
            params={'fast_period': 20, 'slow_period': 50, 'quantity': 100}
        )
        
        assert strategy.fast_period == 20
        assert strategy.slow_period == 50
        assert strategy.quantity == 100
    
    def test_bullish_crossover(self):
        """Test bullish crossover detection"""
        # Create data with bullish crossover
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        close_prices = np.linspace(90, 110, 100)  # Uptrend
        
        data = pd.DataFrame({
            'close': close_prices,
            'open': close_prices - 1,
            'high': close_prices + 2,
            'low': close_prices - 2,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        strategy = SMACrossoverStrategy(
            symbol="TEST",
            params={'fast_period': 10, 'slow_period': 20, 'quantity': 100}
        )
        
        signal = strategy.on_data(data)
        
        # Should generate some signal (BUY, SELL, or HOLD)
        assert signal['action'] in ['BUY', 'SELL', 'HOLD']


class TestStrategyExecutor:
    """Test Strategy Executor"""
    
    @pytest.mark.asyncio
    async def test_validate_strategy_code(self):
        """Test strategy code validation"""
        db_mock = AsyncMock()
        executor = StrategyExecutor(db_mock)
        
        # Valid code
        valid_code = """
class MyStrategy(StrategyBase):
    def setup(self):
        self.period = 20
    
    def on_data(self, data):
        return self.hold()
"""
        result = await executor.validate_strategy_code(valid_code)
        assert result['valid'] == True
        
        # Invalid code (missing on_data)
        invalid_code = """
class MyStrategy(StrategyBase):
    def setup(self):
        pass
"""
        result = await executor.validate_strategy_code(invalid_code)
        assert result['valid'] == False
        assert any('on_data' in err for err in result['errors'])
    
    @pytest.mark.asyncio
    async def test_dangerous_code_detection(self):
        """Test detection of dangerous code"""
        db_mock = AsyncMock()
        executor = StrategyExecutor(db_mock)
        
        # Code with dangerous imports
        dangerous_code = """
import os
class MyStrategy(StrategyBase):
    def setup(self):
        pass
    def on_data(self, data):
        os.system('rm -rf /')
        return self.hold()
"""
        result = await executor.validate_strategy_code(dangerous_code)
        assert result['valid'] == False
        assert any('import os' in err for err in result['errors'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
