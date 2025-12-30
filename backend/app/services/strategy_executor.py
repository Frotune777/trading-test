"""
Strategy Executor
Loads, compiles, and executes user-defined strategies
"""

import logging
import importlib.util
import sys
from typing import Dict, Any, Optional, Type
from datetime import datetime
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.strategy_dsl import StrategyBase
from app.database.models_strategy import Strategy

logger = logging.getLogger(__name__)


class StrategyExecutor:
    """
    Execute user-defined strategies safely.
    
    Features:
    - Load strategy code from database
    - Compile and validate strategy
    - Execute with historical/live data
    - Track performance
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._loaded_strategies: Dict[int, Type[StrategyBase]] = {}
    
    async def load_strategy(self, strategy_id: int) -> Optional[Type[StrategyBase]]:
        """
        Load strategy from database.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Strategy class or None if not found
        """
        try:
            # Fetch strategy from database
            stmt = select(Strategy).where(Strategy.id == strategy_id)
            result = await self.db.execute(stmt)
            strategy_record = result.scalar_one_or_none()
            
            if not strategy_record:
                logger.error(f"Strategy {strategy_id} not found")
                return None
            
            # Check if already loaded
            if strategy_id in self._loaded_strategies:
                return self._loaded_strategies[strategy_id]
            
            # Get strategy code
            strategy_code = strategy_record.strategy_code
            
            if not strategy_code:
                logger.error(f"Strategy {strategy_id} has no code")
                return None
            
            # Compile strategy
            strategy_class = self._compile_strategy(
                strategy_code,
                strategy_record.name
            )
            
            if strategy_class:
                self._loaded_strategies[strategy_id] = strategy_class
                logger.info(f"✅ Loaded strategy: {strategy_record.name}")
            
            return strategy_class
            
        except Exception as e:
            logger.error(f"Error loading strategy {strategy_id}: {e}")
            return None
    
    def _compile_strategy(
        self,
        code: str,
        strategy_name: str
    ) -> Optional[Type[StrategyBase]]:
        """
        Compile strategy code safely.
        
        Args:
            code: Python code
            strategy_name: Strategy name
            
        Returns:
            Strategy class or None if compilation fails
        """
        try:
            # Create module
            module_name = f"user_strategy_{strategy_name.replace(' ', '_')}"
            spec = importlib.util.spec_from_loader(module_name, loader=None)
            module = importlib.util.module_from_spec(spec)
            
            # Add StrategyBase to module namespace
            module.__dict__['StrategyBase'] = StrategyBase
            module.__dict__['pd'] = pd
            
            # Execute code
            exec(code, module.__dict__)
            
            # Find strategy class
            strategy_class = None
            for name, obj in module.__dict__.items():
                if (isinstance(obj, type) and 
                    issubclass(obj, StrategyBase) and 
                    obj is not StrategyBase):
                    strategy_class = obj
                    break
            
            if not strategy_class:
                logger.error(f"No StrategyBase subclass found in {strategy_name}")
                return None
            
            logger.info(f"✅ Compiled strategy: {strategy_name}")
            return strategy_class
            
        except Exception as e:
            logger.error(f"Error compiling strategy {strategy_name}: {e}")
            return None
    
    async def execute_strategy(
        self,
        strategy_id: int,
        symbol: str,
        data: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute strategy with data.
        
        Args:
            strategy_id: Strategy ID
            symbol: Trading symbol
            data: Historical price data
            params: Strategy parameters
            
        Returns:
            Signal dict or None
        """
        try:
            # Load strategy
            strategy_class = await self.load_strategy(strategy_id)
            
            if not strategy_class:
                return None
            
            # Instantiate strategy
            strategy_instance = strategy_class(symbol=symbol, params=params or {})
            
            # Execute strategy
            signal = strategy_instance.on_data(data)
            
            logger.info(
                f"📊 Strategy {strategy_id} signal for {symbol}: {signal.get('action')}"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error executing strategy {strategy_id}: {e}")
            return None
    
    async def validate_strategy_code(self, code: str) -> Dict[str, Any]:
        """
        Validate strategy code before saving.
        
        Args:
            code: Python code
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        try:
            # Try to compile
            compile(code, '<string>', 'exec')
            
            # Check for dangerous imports/functions
            dangerous_keywords = [
                'import os',
                'import sys',
                'import subprocess',
                'exec(',
                'eval(',
                '__import__',
                'open(',
                'file(',
            ]
            
            for keyword in dangerous_keywords:
                if keyword in code:
                    errors.append(f"Dangerous keyword detected: {keyword}")
            
            # Check for StrategyBase inheritance
            if 'class' not in code or 'StrategyBase' not in code:
                warnings.append("Strategy should inherit from StrategyBase")
            
            # Check for required methods
            if 'def setup(self)' not in code:
                warnings.append("Strategy should implement setup() method")
            
            if 'def on_data(self' not in code:
                errors.append("Strategy must implement on_data() method")
            
        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        is_valid = len(errors) == 0
        
        return {
            'valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }
    
    async def backtest_strategy(
        self,
        strategy_id: int,
        symbol: str,
        historical_data: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None,
        initial_capital: float = 100000.0,
        slippage_pct: float = 0.001,
        commission_fixed: float = 20.0
    ) -> Dict[str, Any]:
        """
        Backtest strategy on historical data with realistic simulation.
        """
        try:
            # Load strategy
            strategy_class = await self.load_strategy(strategy_id)
            
            if not strategy_class:
                return {"error": "Strategy not found"}
            
            # Instantiate strategy
            strategy = strategy_class(symbol=symbol, params=params or {})
            
            # Run backtest
            trades = []
            equity_curve = []
            returns = []
            capital = initial_capital
            
            # Simplified position management for backtest
            position = 0  # 1 for Long, -1 for Short, 0 for Flat
            entry_price = 0.0
            entry_time = None
            
            # Start from enough data for indicators (default 50)
            start_idx = min(50, len(historical_data) // 4)
            
            for i in range(start_idx, len(historical_data)):
                # Get data window
                data_window = historical_data.iloc[:i+1]
                current_price = data_window['close'].iloc[-1]
                current_time = data_window.index[-1]
                
                # Execute strategy logic
                signal = strategy.on_data(data_window)
                action = signal.get('action', 'HOLD')
                
                # Handle signals
                if action == 'BUY' and position <= 0:
                    # Close short if exists
                    if position < 0:
                        exit_p = current_price * (1 + slippage_pct)
                        pnl = (entry_price - exit_p) / entry_price
                        trade_gain = (initial_capital * 0.25) * pnl - commission_fixed
                        capital += trade_gain
                        returns.append(pnl)
                        trades.append({
                            'exit_timestamp': current_time,
                            'action': 'EXIT_SHORT',
                            'price': exit_p,
                            'pnl': trade_gain,
                            'pnl_pct': pnl * 100
                        })
                    
                    # Open long
                    position = 1
                    entry_price = current_price * (1 + slippage_pct)
                    capital -= commission_fixed # Entry commission
                    entry_time = current_time
                
                elif action == 'SELL' and position >= 0:
                    # Close long if exists
                    if position > 0:
                        exit_p = current_price * (1 - slippage_pct)
                        pnl = (exit_p - entry_price) / entry_price
                        trade_gain = (initial_capital * 0.25) * pnl - commission_fixed
                        capital += trade_gain
                        returns.append(pnl)
                        trades.append({
                            'exit_timestamp': current_time,
                            'action': 'EXIT_LONG',
                            'price': exit_p,
                            'pnl': trade_gain,
                            'pnl_pct': pnl * 100
                        })
                    
                    # Open short
                    position = -1
                    entry_price = current_price * (1 - slippage_pct)
                    capital -= commission_fixed # Entry commission
                    entry_time = current_time
                
                elif action == 'EXIT' and position != 0:
                    if position > 0:
                        exit_p = current_price * (1 - slippage_pct)
                        pnl = (exit_p - entry_price) / entry_price
                        action_name = 'EXIT_LONG'
                    else:
                        exit_p = current_price * (1 + slippage_pct)
                        pnl = (entry_price - exit_p) / entry_price
                        action_name = 'EXIT_SHORT'
                    
                    trade_gain = (initial_capital * 0.25) * pnl - commission_fixed
                    capital += trade_gain
                    returns.append(pnl)
                    trades.append({
                        'exit_timestamp': current_time,
                        'action': action_name,
                        'price': exit_p,
                        'pnl': trade_gain,
                        'pnl_pct': pnl * 100
                    })
                    position = 0
                
                # Update equity curve
                # If in position, calculate floating P&L
                current_equity = capital
                if position > 0:
                    current_equity += (initial_capital * 0.25) * ((current_price - entry_price) / entry_price)
                elif position < 0:
                    current_equity += (initial_capital * 0.25) * ((entry_price - current_price) / entry_price)
                
                equity_curve.append({
                    'date': current_time.isoformat() if hasattr(current_time, 'isoformat') else str(current_time),
                    'value': float(current_equity)
                })
            
            # Calculate final metrics
            total_trades = len(trades)
            final_capital = capital
            
            # Use shared logic for advanced metrics
            import numpy as np
            values = [p['value'] for p in equity_curve]
            
            # Helper for advanced metrics (duplicated for now, could be in a utils)
            metrics = self._calculate_metrics(values, returns, initial_capital)
            
            return {
                'symbol': symbol,
                'total_trades': total_trades,
                'equity_curve': equity_curve,
                'trades': trades[-20:],  # Last 20 trades for display
                'final_capital': float(final_capital),
                'sharpe': metrics['sharpe'],
                'sortino': metrics['sortino'],
                'calmar': metrics['calmar'],
                'max_drawdown': metrics['max_drawdown'] * 100
            }
            
        except Exception as e:
            logger.error(f"Error backtesting strategy {strategy_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}

    def _calculate_metrics(self, equity_curve: list, returns: list, initial_capital: float) -> dict:
        """Calculate advanced backtest metrics."""
        import numpy as np
        
        if not returns or len(returns) < 2:
            return {"sharpe": 0.0, "sortino": 0.0, "calmar": 0.0, "max_drawdown": 0.0}
            
        returns_array = np.array(returns)
        avg_return = np.mean(returns_array)
        std_dev = np.std(returns_array)
        
        # Risk-free rate (assumed 5% annually)
        rf_daily = 0.0002
        
        sharpe = (avg_return - rf_daily) / std_dev * np.sqrt(252) if std_dev != 0 else 0
        
        downside_returns = returns_array[returns_array < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        sortino = (avg_return - rf_daily) / downside_std * np.sqrt(252) if downside_std != 0 else 0
        
        # Max Drawdown
        peak = initial_capital
        max_dd = 0
        for v in equity_curve:
            if v > peak: peak = v
            dd = (peak - v) / peak if peak != 0 else 0
            if dd > max_dd: max_dd = dd
            
        try:
            total_return = (equity_curve[-1] - initial_capital) / initial_capital
            days = len(equity_curve)
            ann_return = ((1 + total_return) ** (252 / days) - 1) if days > 0 else 0
            calmar = ann_return / max_dd if max_dd > 1e-4 else 0
        except:
            calmar = 0
            
        return {
            "sharpe": float(sharpe),
            "sortino": float(sortino),
            "calmar": float(calmar),
            "max_drawdown": float(max_dd)
        }
