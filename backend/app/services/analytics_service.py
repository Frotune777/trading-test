# app/services/analytics_service.py

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class PostTradeAnalytics:
    """
    Analyzes trade history to calculate performance metrics and reconstruct trade logs.
    """
    def __init__(self, db_path: str = "stock_data.db"):
        self.db = DatabaseManager(db_path)

    def calculate_performance_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate Sharpe Ratio, Max Drawdown, Win Rate, etc.
        """
        query = """
            SELECT created_at, symbol, order_type, quantity, price 
            FROM order_executions
            WHERE (execution_status='LIVE' OR execution_status='DRY_RUN')
            AND created_at >= date('now', ?)
            ORDER BY created_at ASC
        """
        trades = self.db.query_dict(query, (f"-{days} days",))
        if not trades:
            return {"status": "NO_DATA"}

        df = pd.DataFrame(trades)
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Helper: Calculate equity curve
        equity_curve, daily_returns = self._generate_equity_curve(df)
        
        if len(daily_returns) < 2:
             return {"status": "INSUFFICIENT_DATA"}

        # Metrics
        win_rate = self._calculate_win_rate(df)
        sharpe = self._calculate_sharpe_ratio(daily_returns)
        max_dd = self._calculate_max_drawdown(equity_curve)
        
        return {
            "total_trades": len(df),
            "win_rate": win_rate,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "total_pnl": equity_curve[-1] if len(equity_curve) > 0 else 0,
            "period_days": days
        }

    def generate_trade_replay(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Chronological log of trades with running exposure and P&L.
        """
        query = """
            SELECT * FROM order_executions 
            WHERE (execution_status='LIVE' OR execution_status='DRY_RUN')
        """
        params = []
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        query += " ORDER BY created_at ASC"
        
        trades = self.db.query_dict(query, tuple(params))
        replay = []
        running_pnl = 0.0
        positions = {} # symbol -> [qty, avg_price]

        for t in trades:
            sym = t['symbol']
            qty = t['quantity']
            price = t['price']
            action = t['order_type']
            
            pnl_gain = 0.0
            if sym not in positions:
                positions[sym] = [0, 0.0]
            
            curr_qty, curr_avg = positions[sym]
            
            if action == 'BUY':
                if curr_qty < 0: # Closing a short
                    closed_qty = min(qty, abs(curr_qty))
                    pnl_gain = closed_qty * (curr_avg - price)
                
                # Update avg price for new long or remaining short
                new_qty = curr_qty + qty
                if new_qty > 0:
                     # New long or adding to long
                     new_avg = (curr_qty * curr_avg + qty * price) / new_qty if new_qty != 0 else 0
                else: 
                     new_avg = curr_avg # Short partially covered
                
                positions[sym] = [new_qty, new_avg]
            
            else: # SELL
                if curr_qty > 0: # Closing a long
                    closed_qty = min(qty, curr_qty)
                    pnl_gain = closed_qty * (price - curr_avg)
                
                new_qty = curr_qty - qty
                if new_qty < 0:
                    # New short or adding to short
                    new_avg = (abs(curr_qty) * curr_avg + qty * price) / abs(new_qty) if new_qty != 0 else 0
                else:
                    new_avg = curr_avg # Long partially sold
                
                positions[sym] = [new_qty, new_avg]

            running_pnl += pnl_gain
            replay.append({
                "timestamp": t['created_at'],
                "symbol": sym,
                "action": action,
                "qty": qty,
                "price": price,
                "realized_pnl": pnl_gain,
                "running_total_pnl": running_pnl,
                "net_position": positions[sym][0]
            })
            
        return replay

    def _generate_equity_curve(self, df: pd.DataFrame) -> tuple[List[float], pd.Series]:
        """Simple daily P&L aggregation."""
        df['date'] = df['created_at'].dt.date
        # Approximation: group by day, calculate net change
        # A real one needs MTM. Here we just sum realized P&Ls
        # Since our trades don't have Exit Price in the same row, 
        # we'll use a simplified version of generate_trade_replay logic daily.
        replay = self.generate_trade_replay()
        if not replay:
            return [], pd.Series()
        
        replay_df = pd.DataFrame(replay)
        replay_df['date'] = pd.to_datetime(replay_df['timestamp']).dt.date
        daily_pnl = replay_df.groupby('date')['realized_pnl'].sum()
        equity_curve = daily_pnl.cumsum().tolist()
        return equity_curve, daily_pnl

    def _calculate_win_rate(self, df: pd.DataFrame) -> float:
        replay = self.generate_trade_replay()
        closed_trades = [r['realized_pnl'] for r in replay if r['realized_pnl'] != 0]
        if not closed_trades:
            return 0.0
        wins = len([p for p in closed_trades if p > 0])
        return wins / len(closed_trades)

    def _calculate_sharpe_ratio(self, daily_returns: pd.Series) -> float:
        if daily_returns.std() == 0:
            return 0.0
        # Annualized Sharpe (assuming 252 trading days)
        return (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)

    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        if not equity_curve:
            return 0.0
        peak = -np.inf
        max_dd = 0.0
        for val in equity_curve:
            if val > peak:
                peak = val
            dd = peak - val
            if dd > max_dd:
                max_dd = dd
        return max_dd
