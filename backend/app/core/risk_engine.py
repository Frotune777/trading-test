# app/core/risk_engine.py

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.core.redis import redis_client
from app.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class RiskEngine:
    """
    Account-level risk management layer.
    Tracks P&L, exposure, and trade frequency across the whole account.
    Blocks execution if limits are breached.
    """
    # Thresholds (Configurable)
    MAX_DAILY_LOSS = -50000.0 # Stop if lost 50k INR today
    MAX_ACCOUNT_EXPOSURE = 2000000.0 # 20 Lakh INR total notional
    MAX_TRADES_PER_DAY = 50
    
    def __init__(self, db_path: str = "stock_data.db"):
        self.db = DatabaseManager(db_path)

    async def check_risk(self, symbol: str, quantity: int, price: float) -> tuple[bool, Optional[str]]:
        """
        Pre-trade risk check.
        Returns (is_safe, block_reason)
        """
        # 1. Daily Trade Count Check
        today_trades = await self._get_today_trade_count()
        if today_trades >= self.MAX_TRADES_PER_DAY:
            return False, f"RISK_LIMIT_REACHED: Daily trade count ({today_trades}) >= {self.MAX_TRADES_PER_DAY}"

        # 2. Daily P&L Check (Placeholder - would usually come from Broker/Position service)
        # For now, we simulate by checking realized P&L from our audit logs for today
        daily_pnl = await self._calculate_simulated_realized_pnl()
        if daily_pnl <= self.MAX_DAILY_LOSS:
            return False, f"RISK_LIMIT_REACHED: Daily loss limit ({daily_pnl:.0f}) <= {self.MAX_DAILY_LOSS}"

        # 3. Exposure Check
        total_exposure = await self._calculate_current_exposure()
        new_trade_notional = quantity * price
        if total_exposure + new_trade_notional > self.MAX_ACCOUNT_EXPOSURE:
            return False, f"RISK_LIMIT_REACHED: Max exposure ({total_exposure + new_trade_notional:.0f}) > {self.MAX_ACCOUNT_EXPOSURE}"

        return True, None

    async def _get_today_trade_count(self) -> int:
        """Count today's successful executions."""
        query = "SELECT COUNT(*) as count FROM order_executions WHERE (execution_status='LIVE' OR execution_status='DRY_RUN') AND created_at >= date('now')"
        res = self.db.query_dict(query)
        return res[0]['count'] if res else 0

    async def _calculate_simulated_realized_pnl(self) -> float:
        """
        Simulate daily P&L based on our audit logs.
        In a real system, this fetches from the PositionManager or Broker API.
        We calculate this by matching BUYs and SELLs for the same symbol today.
        """
        query = """
            SELECT symbol, order_type, quantity, price 
            FROM order_executions 
            WHERE (execution_status='LIVE' OR execution_status='DRY_RUN') 
            AND created_at >= date('now')
            ORDER BY created_at ASC
        """
        trades = self.db.query_dict(query)
        if not trades:
            return 0.0

        # Calculate realized P&L (FIFO-ish logic for simulation)
        pnl = 0.0
        positions = {} # symbol -> [quantity, price] (net position for P&L tracking)
        
        for t in trades:
            symbol = t['symbol']
            qty = t['quantity']
            price = t['price']
            action = t['order_type']

            if symbol not in positions:
                positions[symbol] = 0
            
            # Simple Realized P&L approximation:
            # We track the net quantity. If it changes sign or goes to zero, we've "closed" some part.
            # For simplicity in this audit-based sim, we'll just use a running cash balance approach:
            if action == 'BUY':
                pnl -= qty * price
                positions[symbol] += qty
            else: # SELL
                pnl += qty * price
                positions[symbol] -= qty

        # Add back current mark-to-market for open positions? 
        # Realized P&L usually only counts closed trades. 
        # But for risk, we often care about Total P&L (Realized + Unrealized).
        # Let's stick to simple "Net Cash Flow" for today's trades as a proxy for Daily P&L 
        # if we assume we start flat every day.
        
        # To make it strictly "Realized", we'd need to subtract the value of open positions.
        for symbol, net_qty in positions.items():
            if net_qty != 0:
                # Subtract (or add) the current value of the open position to get only realized P&L
                # We'll use the last trade price as a proxy for current price
                last_price = next((t['price'] for t in reversed(trades) if t['symbol'] == symbol), 0)
                pnl += net_qty * last_price # This cancels out the cost of the open part

        return pnl

    async def _calculate_current_exposure(self) -> float:
        """
        Estimate current open exposure (Total Notional Value of open positions).
        """
        query = """
            SELECT symbol, SUM(CASE WHEN order_type='BUY' THEN quantity ELSE -quantity END) as net_qty
            FROM order_executions 
            WHERE (execution_status='LIVE' OR execution_status='DRY_RUN') 
            AND created_at >= date('now')
            GROUP BY symbol
            HAVING net_qty != 0
        """
        positions = self.db.query_dict(query)
        if not positions:
            # If no trades today, check Redis for persistent exposure or previous days
            cached = await redis_client.get("risk:account_exposure")
            return float(cached) if cached else 0.0

        total_exposure = 0.0
        for pos in positions:
            symbol = pos['symbol']
            net_qty = abs(pos['net_qty'])
            
            # Fetch latest price from Redis or last execution
            price = 0.0
            try:
                cached_ltp = await redis_client.get(f"market:ltp:NSE:{symbol}")
                if cached_ltp:
                    price = json.loads(cached_ltp).get('ltp', 0)
            except: pass
            
            if price == 0:
                # Fallback to last execution price
                latest = self.db.query_dict("SELECT price FROM order_executions WHERE symbol=? ORDER BY created_at DESC LIMIT 1", (symbol,))
                price = latest[0]['price'] if latest else 0.0
            
            total_exposure += net_qty * price

        return total_exposure

    async def update_exposure_cache(self, exposure: float):
        """Update the exposure cache from position manager."""
        await redis_client.set("risk:account_exposure", str(exposure), ex=3600)
