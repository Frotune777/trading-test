"""
Unit tests for Phase 2.1 Strategy Code Validation and Execution
Tests the strategy_executor service directly without API layer
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.services.strategy_executor import StrategyExecutor
from app.services.strategy_dsl import StrategyBase


class TestStrategyCodeValidation:
    """Test strategy code validation"""
    
    @pytest.mark.asyncio
    async def test_validate_valid_code(self):
        """Test validation of valid strategy code"""
        db_mock = AsyncMock()
        executor = StrategyExecutor(db_mock)
        
        valid_code = """
class MyStrategy(StrategyBase):
    def setup(self):
        self.period = 20
    
    def on_data(self, data):
        return self.hold()
"""
        result = await executor.validate_strategy_code(valid_code)
        
        assert result['valid'] == True
        assert len(result['errors']) == 0
        assert 'timestamp' in result
    
    @pytest.mark.asyncio
    async def test_validate_syntax_error(self):
        """Test validation catches syntax errors"""
        db_mock = AsyncMock()
        executor = StrategyExecutor(db_mock)
        
        invalid_code = """
class MyStrategy(StrategyBase):
    def setup(self)  # Missing colon
        self.period = 20
"""
        result = await executor.validate_strategy_code(invalid_code)
        
        assert result['valid'] == False
        assert len(result['errors']) > 0
        assert any('Syntax error' in err for err in result['errors'])
    
    @pytest.mark.asyncio
    async def test_validate_dangerous_imports(self):
        """Test validation blocks dangerous imports"""
        db_mock = AsyncMock()
        executor = StrategyExecutor(db_mock)
        
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
    
    @pytest.mark.asyncio
    async def test_validate_missing_on_data(self):
        """Test validation requires on_data method"""
        db_mock = AsyncMock()
        executor = StrategyExecutor(db_mock)
        
        incomplete_code = """
class MyStrategy(StrategyBase):
    def setup(self):
        pass
"""
        result = await executor.validate_strategy_code(incomplete_code)
        
        assert result['valid'] == False
        assert any('on_data' in err for err in result['errors'])
    
    @pytest.mark.asyncio
    async def test_validate_multiple_dangerous_keywords(self):
        """Test validation catches multiple dangerous keywords"""
        db_mock = AsyncMock()
        executor = StrategyExecutor(db_mock)
        
        dangerous_code = """
import sys
import subprocess
class MyStrategy(StrategyBase):
    def setup(self):
        exec('malicious code')
    def on_data(self, data):
        eval('more malicious code')
        return self.hold()
"""
        result = await executor.validate_strategy_code(dangerous_code)
        
        assert result['valid'] == False
        assert len(result['errors']) >= 4  # import sys, subprocess, exec, eval


class TestStrategyBacktest:
    """Test strategy backtesting functionality"""
    
    @pytest.mark.asyncio
    async def test_backtest_with_valid_strategy(self):
        """Test backtesting a valid strategy"""
        db_mock = AsyncMock()
        executor = StrategyExecutor(db_mock)
        
        # Create sample historical data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        historical_data = pd.DataFrame({
            'close': np.linspace(100, 120, 100),
            'open': np.linspace(99, 119, 100),
            'high': np.linspace(101, 121, 100),
            'low': np.linspace(98, 118, 100),
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        # Mock strategy loading
        class TestStrategy(StrategyBase):
            def setup(self):
                self.period = 20
            
            def on_data(self, data):
                return self.hold()
        
        executor._loaded_strategies = {1: TestStrategy}
        
        result = await executor.backtest_strategy(
            strategy_id=1,
            symbol="TEST",
            historical_data=historical_data
        )
        
        assert 'symbol' in result
        assert result['symbol'] == "TEST"
        assert 'total_trades' in result
        assert 'equity_curve' in result
        assert 'final_capital' in result
        assert 'sharpe' in result
        assert 'max_drawdown' in result
        assert isinstance(result['equity_curve'], list)
        assert isinstance(result['equity_curve'][0], dict)
        assert 'date' in result['equity_curve'][0]
        assert 'value' in result['equity_curve'][0]


class TestStrategyExecution:
    """Test strategy execution"""
    
    @pytest.mark.asyncio
    async def test_execute_hold_strategy(self):
        """Test executing a strategy that returns HOLD"""
        db_mock = AsyncMock()
        executor = StrategyExecutor(db_mock)
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        data = pd.DataFrame({
            'close': np.linspace(100, 110, 50),
            'open': np.linspace(99, 109, 50),
            'high': np.linspace(101, 111, 50),
            'low': np.linspace(98, 108, 50),
            'volume': np.random.randint(1000, 10000, 50)
        }, index=dates)
        
        # Mock strategy
        class HoldStrategy(StrategyBase):
            def setup(self):
                pass
            
            def on_data(self, data):
                return self.hold()
        
        executor._loaded_strategies = {1: HoldStrategy}
        
        signal = await executor.execute_strategy(
            strategy_id=1,
            symbol="TEST",
            data=data
        )
        
        assert signal is not None
        assert signal['action'] == 'HOLD'


class TestStrategyCompilation:
    """Test strategy code compilation"""
    
    def test_compile_valid_strategy(self):
        """Test compiling valid strategy code"""
        db_mock = AsyncMock()
        executor = StrategyExecutor(db_mock)
        
        code = """
class TestStrategy(StrategyBase):
    def setup(self):
        self.period = 20
    
    def on_data(self, data):
        return self.hold()
"""
        strategy_class = executor._compile_strategy(code, "TestStrategy")
        
        assert strategy_class is not None
        assert issubclass(strategy_class, StrategyBase)
    
    def test_compile_invalid_strategy(self):
        """Test compiling invalid strategy code returns None"""
        db_mock = AsyncMock()
        executor = StrategyExecutor(db_mock)
        
        invalid_code = """
class TestStrategy:  # Not inheriting from StrategyBase
    pass
"""
        strategy_class = executor._compile_strategy(invalid_code, "TestStrategy")
        
        # Should return None or handle error gracefully
        assert strategy_class is None or not issubclass(strategy_class, StrategyBase)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
