"""
Enhanced Backtest Engine
Reuses live execution logic for realistic simulation
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.backtest_service import BacktestService
from app.services.risk_manager import RiskManager
from app.brokers.base_adapter import Order

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Enhanced backtest engine that reuses live execution logic.
    
    Compliance:
    - Rule #29: Shared logic reuse (uses RiskManager)
    - Rule #25: Deterministic behavior
    - Rule #28: Timezone-aware (IST)
    """
    
    # Simulation parameters
    SLIPPAGE_BPS = 5  # 0.05% slippage for market orders
    COMMISSION_BPS = 3  # 0.03% commission per trade
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.backtest_service = BacktestService(db)
        self.risk_manager = RiskManager()
    
    async def validate_backtest_order(
        self,
        order: Order,
        user_id: int,
        mode: str = "BACKTEST"
    ) -> Dict[str, Any]:
        """
        Validate order using live RiskManager logic.
        
        Args:
            order: Order to validate
            user_id: User ID
            mode: Execution mode (BACKTEST)
            
        Returns:
            Validation result from RiskManager
        """
        # Use the same RiskManager as live trading
        # This ensures consistent risk checks
        result = await self.risk_manager.validate_order(
            order=order,
            db=self.db,
            user_id=user_id
        )
        
        # Add backtest-specific metadata
        result["mode"] = mode
        result["simulated"] = True
        
        return result
    
    def calculate_realistic_fill_price(
        self,
        order_price: float,
        order_type: str,
        transaction_type: str
    ) -> float:
        """
        Calculate realistic fill price with slippage.
        
        Args:
            order_price: Order price
            order_type: MARKET or LIMIT
            transaction_type: BUY or SELL
            
        Returns:
            Realistic fill price
        """
        if order_type == "MARKET":
            # Apply slippage for market orders
            slippage_factor = self.SLIPPAGE_BPS / 10000
            
            if transaction_type == "BUY":
                # Buy at slightly higher price
                return order_price * (1 + slippage_factor)
            else:
                # Sell at slightly lower price
                return order_price * (1 - slippage_factor)
        else:
            # Limit orders fill at limit price (if filled)
            return order_price
    
    def calculate_commission(self, trade_value: float) -> float:
        """
        Calculate commission for a trade.
        
        Args:
            trade_value: Total trade value
            
        Returns:
            Commission amount
        """
        return trade_value * (self.COMMISSION_BPS / 10000)
    
    def calculate_trade_pnl(
        self,
        entry_price: float,
        exit_price: float,
        quantity: int,
        transaction_type: str
    ) -> Dict[str, float]:
        """
        Calculate trade P&L with commissions.
        
        Args:
            entry_price: Entry price
            exit_price: Exit price
            quantity: Quantity
            transaction_type: BUY or SELL
            
        Returns:
            Dict with gross_pnl, commission, net_pnl
        """
        entry_value = entry_price * quantity
        exit_value = exit_price * quantity
        
        # Calculate gross P&L
        if transaction_type == "BUY":
            gross_pnl = exit_value - entry_value
        else:  # SELL (short)
            gross_pnl = entry_value - exit_value
        
        # Calculate commissions (entry + exit)
        entry_commission = self.calculate_commission(entry_value)
        exit_commission = self.calculate_commission(exit_value)
        total_commission = entry_commission + exit_commission
        
        # Net P&L
        net_pnl = gross_pnl - total_commission
        
        return {
            "gross_pnl": gross_pnl,
            "commission": total_commission,
            "net_pnl": net_pnl,
            "pnl_percent": (net_pnl / entry_value * 100) if entry_value > 0 else 0
        }
    
    def calculate_performance_metrics(
        self,
        equity_curve: List[float],
        trades: List[Dict[str, Any]],
        initial_capital: float
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics.
        
        Args:
            equity_curve: List of equity values
            trades: List of trade records
            initial_capital: Starting capital
            
        Returns:
            Dict with performance metrics
        """
        import numpy as np
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get("net_pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("net_pnl", 0) < 0]
        
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = sum(t.get("net_pnl", 0) for t in trades)
        avg_win = np.mean([t["net_pnl"] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t["net_pnl"] for t in losing_trades]) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(t["net_pnl"] for t in winning_trades)
        gross_loss = abs(sum(t["net_pnl"] for t in losing_trades))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        # Drawdown
        peak = equity_curve[0]
        max_drawdown = 0
        max_drawdown_pct = 0
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = peak - equity
            drawdown_pct = (drawdown / peak * 100) if peak > 0 else 0
            
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct
        
        # Returns
        returns = np.diff(equity_curve) / equity_curve[:-1]
        
        # Sharpe Ratio (annualized, assuming 252 trading days)
        if len(returns) > 0:
            mean_return = np.mean(returns) * 252
            std_return = np.std(returns) * np.sqrt(252)
            sharpe_ratio = (mean_return / std_return) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_std = np.std(downside_returns) * np.sqrt(252)
            sortino_ratio = (mean_return / downside_std) if downside_std > 0 else 0
        else:
            sortino_ratio = 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "total_return_pct": (total_pnl / initial_capital * 100),
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "max_drawdown_pct": max_drawdown_pct,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio
        }
