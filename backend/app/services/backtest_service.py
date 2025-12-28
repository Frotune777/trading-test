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
        initial_capital: float = 100000.0
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
            
        result = await self.db.execute(stmt)
        decisions = result.scalars().all()
        
        if not decisions:
            return {
                "symbol": symbol,
                "win_rate": 0.0,
                "total_trades": 0,
                "avg_return": 0.0,
                "max_drawdown": 0.0,
                "equity_curve": []
            }
            
        # 2. Get price history for benchmarking and trade evaluation
        price_stmt = text("""
            SELECT date, close FROM price_history 
            WHERE symbol = :symbol 
            ORDER BY date ASC
        """)
        price_result = await self.db.execute(price_stmt, {"symbol": symbol.upper()})
        price_data = price_result.fetchall()
        
        if not price_data:
            return {"error": "No price history found for benchmarking"}
            
        prices_df = pd.DataFrame(price_data, columns=['date', 'close'])
        prices_df['date'] = pd.to_datetime(prices_df['date'])
        prices_df.set_index('date', inplace=True)
        
        # 3. Simulate trades
        # We assume entry at the decision timestamp price (or close) 
        # and exit after a fixed window (e.g., 5 days) or next signal
        trades = []
        equity = initial_capital
        equity_curve = []
        
        # Initial points
        first_date = decisions[0].timestamp.date()
        equity_curve.append({
            "date": first_date.isoformat(),
            "value": float(equity),
            "benchmark_value": float(initial_capital)
        })
        
        benchmark_start_price = float(prices_df.iloc[0]['close']) if not prices_df.empty else 1.0
        
        for i, decision in enumerate(decisions):
            # Evaluate this signal
            # For simplicity, we assume we hold for 5 trading days
            entry_price = float(decision.current_price)
            entry_date = decision.timestamp
            
            # Find exit price (5 days later)
            exit_date = entry_date + timedelta(days=5)
            # Find the closest price record >= exit_date
            future_prices = prices_df[prices_df.index >= pd.Timestamp(exit_date)]
            
            if future_prices.empty:
                # If no future price, we can't evaluate yet
                continue
                
            exit_price = float(future_prices.iloc[0]['close'])
            actual_exit_date = future_prices.index[0]
            
            # Calculate trade P&L
            # Note: This is a very simplified backtest
            change_pct = 0.0
            if decision.signal == 'BUY':
                change_pct = (exit_price - entry_price) / entry_price
            elif decision.signal == 'SELL':
                change_pct = (entry_price - exit_price) / entry_price
            
            # Assume 25% of capital per trade for calculation
            trade_pnl = (equity * 0.25) * change_pct
            equity += trade_pnl
            
            # Benchmark P&L (NIFTY or just buy & hold of this stock)
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
                
        return {
            "symbol": symbol,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "avg_return": avg_return,
            "max_drawdown": max_dd * 100,
            "equity_curve": equity_curve,
            "trades": trades
        }
