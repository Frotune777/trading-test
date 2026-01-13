"""
QUAD Backtest Service
Simulates historical trades based on QUAD signals and calculates equity curve.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, text

from app.database.models_quad import QUADDecision, QUADSignalAccuracy
from app.services.quad_analytics_service import QUADAnalyticsService
import traceback

logger = logging.getLogger(__name__)

class BacktestService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analytics_service = QUADAnalyticsService(db)

    async def get_equity_curve(
        self, 
        symbol: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        initial_capital: float = 100000.0,
        slippage_pct: float = 0.001,  # 0.1% slippage
        commission_fixed: float = 20.0  # ₹20 fixed per trade
    ) -> Dict[str, Any]:
        """
        Calculate equity curve for a symbol based on QUAD signals
        """
        # 1. Get historical decisions
        stmt = select(QUADDecision).where(
            QUADDecision.symbol == symbol.upper()
        ).order_by(QUADDecision.timestamp.asc())
        
        if start_date:
            stmt = stmt.where(QUADDecision.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(QUADDecision.timestamp <= end_date)
            
        try:
            result = await self.db.execute(stmt)
            decisions = result.scalars().all()
        except Exception as e:
            with open("/home/fortune/Desktop/Python_Projects/quad_trading/trading-test/backend/error_log.txt", "a") as f:
                f.write(f"Error in get_equity_curve (decisions): {str(e)}\n")
                f.write(traceback.format_exc())
            raise e
        
        if not decisions:
            return {
                "symbol": symbol,
                "win_rate": 0.0,
                "total_trades": 0,
                "avg_return": 0.0,
                "max_drawdown": 0.0,
                "sharpe": 0.0,
                "sortino": 0.0,
                "calmar": 0.0,
                "equity_curve": []
            }
            
        # 2. Get price history for benchmarking and trade evaluation
        price_stmt = text("""
            SELECT timestamp as date, close FROM historical_ohlc 
            WHERE symbol = :symbol 
            ORDER BY timestamp ASC
        """)
        price_result = await self.db.execute(price_stmt, {"symbol": symbol.upper()})
        price_data = price_result.fetchall()
        
        if not price_data:
            return {"error": "No price history found for benchmarking"}
            
        prices_df = pd.DataFrame(price_data, columns=['date', 'close'])
        prices_df['date'] = pd.to_datetime(prices_df['date'], utc=True)
        prices_df.set_index('date', inplace=True)
        
        # 3. Simulate trades
        trades = []
        equity = initial_capital
        equity_curve = []
        returns = []
        
        # Initial points
        first_date = decisions[0].timestamp.date()
        equity_curve.append({
            "date": first_date.isoformat(),
            "value": float(equity),
            "benchmark_value": float(initial_capital)
        })
        
        benchmark_start_price = float(prices_df.iloc[0]['close']) if not prices_df.empty else 1.0
        
        for i, decision in enumerate(decisions):
            entry_price = float(decision.current_price)
            entry_date = decision.timestamp
            
            # Find exit price (5 days later)
            exit_date = entry_date + timedelta(days=5)
            
            # Ensure exit_date is timezone-aware UTC to match prices_df.index
            # decision.timestamp from DB is timezone-naive, so we localize it to UTC
            if not hasattr(exit_date, 'tzinfo') or exit_date.tzinfo is None:
                # Timezone-naive, assume UTC and localize
                exit_date_ts = pd.Timestamp(exit_date).tz_localize('UTC')
            else:
                # Already timezone-aware, convert to UTC if needed
                exit_date_ts = pd.Timestamp(exit_date).tz_convert('UTC')
            
            # Find the closest price record >= exit_date
            future_prices = prices_df[prices_df.index >= exit_date_ts]
            
            if future_prices.empty:
                continue
                
            exit_price = float(future_prices.iloc[0]['close'])
            actual_exit_date = future_prices.index[0]
            
            # Slippage modeling (Buy at higher, Sell at lower)
            if decision.signal == 'BUY':
                eff_entry = entry_price * (1 + slippage_pct)
                eff_exit = exit_price * (1 - slippage_pct)
                change_pct = (eff_exit - eff_entry) / eff_entry
            elif decision.signal == 'SELL':
                eff_entry = entry_price * (1 - slippage_pct)
                eff_exit = exit_price * (1 + slippage_pct)
                change_pct = (eff_entry - eff_exit) / eff_entry
            else:
                continue
            
            # Apply commission (entry + exit)
            trade_pnl = (equity * 0.25) * change_pct - (2 * commission_fixed)
            equity += trade_pnl
            
            # Calculate daily equivalent return for Sharpe/Sortino
            returns.append(change_pct)
            
            # Benchmark P&L
            benchmark_price = float(future_prices.iloc[0]['close'])
            benchmark_val = initial_capital * (benchmark_price / benchmark_start_price)
            
            trades.append({
                "entry_date": entry_date.isoformat(),
                "exit_date": actual_exit_date.isoformat(),
                "pnl": float(trade_pnl),
                "pnl_pct": float(change_pct * 100),
                "signal": decision.signal,
                "conviction": decision.conviction
            })
            
            equity_curve.append({
                "date": actual_exit_date.date().isoformat(),
                "value": float(equity),
                "benchmark_value": float(benchmark_val)
            })
            
        # 4. Calculate metrics
        total_trades = len(trades)
        wins = len([t for t in trades if t['pnl'] > 0])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        avg_return = sum(t['pnl_pct'] for t in trades) / total_trades if total_trades > 0 else 0
        
        # Max drawdown
        values = [float(p['value']) for p in equity_curve]
        peak = values[0]
        max_dd = 0
        for v in values:
            if v > peak:
                peak = v
            dd = (peak - v) / peak if peak != 0 else 0
            if dd > max_dd:
                max_dd = dd

        # Advanced Metrics
        metrics = self._calculate_advanced_metrics(values, returns, initial_capital)
                
        return {
            "symbol": symbol,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "avg_return": avg_return,
            "max_drawdown": max_dd * 100,
            "sharpe": metrics["sharpe"],
            "sortino": metrics["sortino"],
            "calmar": metrics["calmar"],
            "equity_curve": equity_curve,
            "trades": trades
        }

    def _calculate_advanced_metrics(self, equity_curve: List[float], returns: List[float], initial_capital: float) -> Dict[str, float]:
        """
        Calculate Sharpe, Sortino, and Calmar ratios.
        """
        if not returns or len(returns) < 2:
            return {"sharpe": 0.0, "sortino": 0.0, "calmar": 0.0}
            
        returns_array = np.array(returns)
        avg_return = np.mean(returns_array)
        std_dev = np.std(returns_array)
        
        # Risk-free rate (assumed 5% annually, 0.02% daily)
        rf_daily = 0.0002
        
        # Sharpe Ratio (Annualized)
        sharpe = (avg_return - rf_daily) / std_dev * np.sqrt(252) if std_dev != 0 else 0
        
        # Sortino Ratio (Annualized)
        downside_returns = returns_array[returns_array < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        sortino = (avg_return - rf_daily) / downside_std * np.sqrt(252) if downside_std != 0 else 0
        
        # Max Drawdown for Calmar
        peak = initial_capital
        max_dd = 0
        for v in equity_curve:
            if v > peak: peak = v
            dd = (peak - v) / peak if peak != 0 else 0
            if dd > max_dd: max_dd = dd
            
        # Calmar Ratio (Annualized return / Max DD)
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
            "calmar": float(calmar)
        }

