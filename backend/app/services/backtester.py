from typing import List, Dict, Any
import pandas as pd

class Backtester:
    """
    PILLAR 3: Decision Engine (D) - Backtesting Framework
    Evaluates trading strategies on historical data.
    """
    def __init__(self, initial_capital: float = 1000000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = []
        self.trades = []

    def run(self, df: pd.DataFrame, signals: pd.Series) -> Dict[str, Any]:
        """
        Simple vectorized or loop-based backtest
        signals: Series with 1 (BUY), -1 (SELL), 0 (HOLD)
        """
        # For brevity, a vectorized performance calculation
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['returns'] * signals.shift(1)
        
        cumulative_returns = (1 + df['strategy_returns'].fillna(0)).cumprod()
        final_value = self.initial_capital * cumulative_returns.iloc[-1]
        
        return {
            "initial_capital": self.initial_capital,
            "final_value": float(final_value),
            "total_return_pct": float((final_value/self.initial_capital - 1) * 100),
            "sharpe_ratio": float(df['strategy_returns'].mean() / df['strategy_returns'].std() * (252**0.5)) if df['strategy_returns'].std() != 0 else 0
        }
